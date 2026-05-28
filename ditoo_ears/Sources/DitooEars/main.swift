// DitooEars — clap / loud-transient detector for Clawd, using the Mac's mic.
//
// Modes:
//   ditoo-ears                 Detect claps; print "clap <unix_ms> <peak>" per clap.
//   ditoo-ears meter           Print live RMS levels (for tuning + verifying the mic works).
//
// Options (detect mode):
//   --floor F     absolute RMS floor for a clap (default 0.06)
//   --rise R      current RMS must exceed baseline*R (default 4.0)
//   --debounce MS ignore window after a clap, ms (default 220)
//   --device NAME prefer an input device whose name contains NAME (default: built-in)
//
// We deliberately default to the BUILT-IN mic so listening never degrades the
// Ditoo's A2DP audio (selecting the Ditoo's HFP mic would drop music to call quality).

import Foundation
import AVFoundation
import CoreAudio

let stderrH = FileHandle.standardError
let stdoutH = FileHandle.standardOutput
func log(_ s: String) { stderrH.write((s + "\n").data(using: .utf8)!) }
func emit(_ s: String) { stdoutH.write((s + "\n").data(using: .utf8)!) }

// ---- Core Audio: find a device id by name substring, and the built-in default ----

func allInputDevices() -> [(id: AudioDeviceID, name: String)] {
    var size = UInt32(0)
    var addr = AudioObjectPropertyAddress(
        mSelector: kAudioHardwarePropertyDevices,
        mScope: kAudioObjectPropertyScopeGlobal,
        mElement: kAudioObjectPropertyElementMain)
    AudioObjectGetPropertyDataSize(AudioObjectID(kAudioObjectSystemObject), &addr, 0, nil, &size)
    let count = Int(size) / MemoryLayout<AudioDeviceID>.size
    var ids = [AudioDeviceID](repeating: 0, count: count)
    AudioObjectGetPropertyData(AudioObjectID(kAudioObjectSystemObject), &addr, 0, nil, &size, &ids)

    var result: [(AudioDeviceID, String)] = []
    for id in ids {
        // input channel count > 0 ?
        var sizeIn = UInt32(0)
        var addrIn = AudioObjectPropertyAddress(
            mSelector: kAudioDevicePropertyStreamConfiguration,
            mScope: kAudioDevicePropertyScopeInput,
            mElement: kAudioObjectPropertyElementMain)
        AudioObjectGetPropertyDataSize(id, &addrIn, 0, nil, &sizeIn)
        let bufList = UnsafeMutableRawPointer.allocate(byteCount: Int(sizeIn), alignment: 16)
        defer { bufList.deallocate() }
        AudioObjectGetPropertyData(id, &addrIn, 0, nil, &sizeIn, bufList)
        let abl = bufList.assumingMemoryBound(to: AudioBufferList.self)
        var channels = 0
        let listPtr = UnsafeMutableAudioBufferListPointer(abl)
        for b in listPtr { channels += Int(b.mNumberChannels) }
        if channels <= 0 { continue }

        // name (CFString must be read via Unmanaged to handle the retain correctly)
        var nameRef: Unmanaged<CFString>?
        var nameSize = UInt32(MemoryLayout<Unmanaged<CFString>?>.size)
        var nameAddr = AudioObjectPropertyAddress(
            mSelector: kAudioObjectPropertyName,
            mScope: kAudioObjectPropertyScopeGlobal,
            mElement: kAudioObjectPropertyElementMain)
        let nameStatus = AudioObjectGetPropertyData(id, &nameAddr, 0, nil, &nameSize, &nameRef)
        let name = (nameStatus == noErr) ? (nameRef?.takeRetainedValue() as String? ?? "(unknown)") : "(unknown)"
        result.append((id, name))
    }
    return result
}

func pickInputDevice(preferContains: String?) -> (AudioDeviceID, String)? {
    let inputs = allInputDevices()
    if inputs.isEmpty { return nil }
    if let want = preferContains?.lowercased(), !want.isEmpty {
        if let m = inputs.first(where: { $0.name.lowercased().contains(want) }) { return m }
    }
    // Prefer a built-in mic; avoid the Ditoo (don't degrade its audio).
    if let builtin = inputs.first(where: {
        let n = $0.name.lowercased()
        return (n.contains("macbook") || n.contains("built-in") || n.contains("internal")) &&
               !n.contains("ditoo") && !n.contains("divoom")
    }) { return builtin }
    // Otherwise first non-Ditoo input.
    if let nonDitoo = inputs.first(where: {
        let n = $0.name.lowercased(); return !n.contains("ditoo") && !n.contains("divoom")
    }) { return nonDitoo }
    return inputs.first
}

func setEngineInputDevice(_ engine: AVAudioEngine, deviceID: AudioDeviceID) {
    guard let unit = engine.inputNode.audioUnit else { return }
    var dev = deviceID
    AudioUnitSetProperty(unit,
        kAudioOutputUnitProperty_CurrentDevice,
        kAudioUnitScope_Global, 0,
        &dev, UInt32(MemoryLayout<AudioDeviceID>.size))
}

// ---- argv ----

let args = Array(CommandLine.arguments.dropFirst())
let meterMode = args.first == "meter"
func argVal(_ flag: String, _ def: Float) -> Float {
    if let i = args.firstIndex(of: flag), i + 1 < args.count, let v = Float(args[i+1]) { return v }
    return def
}
func argStr(_ flag: String) -> String? {
    if let i = args.firstIndex(of: flag), i + 1 < args.count { return args[i+1] }
    return nil
}
let absFloor = argVal("--floor", 0.06)
let riseFactor = argVal("--rise", 4.0)
let debounceMs = Int64(argVal("--debounce", 220))
let preferDevice = argStr("--device")

// ---- engine setup ----

let engine = AVAudioEngine()
if let (devID, devName) = pickInputDevice(preferContains: preferDevice) {
    setEngineInputDevice(engine, deviceID: devID)
    log("[ears] input device: \(devName)")
} else {
    log("[ears] no input device found; using engine default")
}

let input = engine.inputNode
let format = input.inputFormat(forBus: 0)
log("[ears] format: \(Int(format.sampleRate))Hz \(format.channelCount)ch  mode=\(meterMode ? "meter" : "clap")")

var baseline: Float = 0.01
var lastClapMs: Int64 = 0
var meterCounter = 0

input.installTap(onBus: 0, bufferSize: 1024, format: format) { buffer, _ in
    guard let ch = buffer.floatChannelData?[0] else { return }
    let n = Int(buffer.frameLength)
    if n == 0 { return }
    var sumSq: Float = 0
    var peak: Float = 0
    for i in 0..<n {
        let s = ch[i]
        sumSq += s * s
        if abs(s) > peak { peak = abs(s) }
    }
    let rms = sqrtf(sumSq / Float(n))
    let nowMs = Int64(Date().timeIntervalSince1970 * 1000)

    if meterMode {
        meterCounter += 1
        if meterCounter % 4 == 0 {   // ~ every few buffers
            let bars = Int(min(40, rms * 200))
            emit(String(format: "rms %.4f peak %.4f  %@", rms, peak, String(repeating: "#", count: bars)))
        }
        return
    }

    let isTransient = rms > absFloor && rms > baseline * riseFactor
    if isTransient && (nowMs - lastClapMs) > debounceMs {
        lastClapMs = nowMs
        emit("clap \(nowMs) \(String(format: "%.3f", peak))")
    }
    // slow baseline (ambient level) tracker
    baseline = baseline * 0.95 + rms * 0.05
}

do {
    try engine.start()
    log("[ears] listening (floor=\(absFloor) rise=\(riseFactor) debounce=\(debounceMs)ms)")
} catch {
    log("[ears] failed to start engine: \(error)")
    exit(2)
}

signal(SIGINT) { _ in exit(0) }
RunLoop.current.run()
