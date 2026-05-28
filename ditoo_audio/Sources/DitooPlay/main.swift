// DitooPlay — play an audio file to a SPECIFIC output device (by name substring),
// independent of the macOS default output. This lets Clawd's sounds come out of
// the Ditoo while your music keeps playing on AirPods/monitors/etc.
//
// Usage:
//   ditoo-play --list                          list output devices
//   ditoo-play --device "DitooPro" sound.wav   play sound.wav to the Ditoo (one-shot)
//   ditoo-play sound.wav                        play to system default
//   ditoo-play --device "DitooPro" --serve     hold engine open; read file paths on
//                                               stdin (one per line) and play each.
//                                               Keeps the A2DP link warm = instant sounds.
//
// No special permissions needed (audio output is not TCC-gated).

import Foundation
import AVFoundation
import CoreAudio

let stderrH = FileHandle.standardError
func log(_ s: String) { stderrH.write((s + "\n").data(using: .utf8)!) }
func out(_ s: String) { FileHandle.standardOutput.write((s + "\n").data(using: .utf8)!) }

// ---- enumerate OUTPUT devices ----

func outputDevices() -> [(id: AudioDeviceID, name: String)] {
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
        // output channel count > 0 ?
        var sizeOut = UInt32(0)
        var addrOut = AudioObjectPropertyAddress(
            mSelector: kAudioDevicePropertyStreamConfiguration,
            mScope: kAudioDevicePropertyScopeOutput,
            mElement: kAudioObjectPropertyElementMain)
        AudioObjectGetPropertyDataSize(id, &addrOut, 0, nil, &sizeOut)
        if sizeOut == 0 { continue }
        let buf = UnsafeMutableRawPointer.allocate(byteCount: Int(sizeOut), alignment: 16)
        defer { buf.deallocate() }
        AudioObjectGetPropertyData(id, &addrOut, 0, nil, &sizeOut, buf)
        let abl = buf.assumingMemoryBound(to: AudioBufferList.self)
        var channels = 0
        for b in UnsafeMutableAudioBufferListPointer(abl) { channels += Int(b.mNumberChannels) }
        if channels <= 0 { continue }

        var nameRef: Unmanaged<CFString>?
        var nameSize = UInt32(MemoryLayout<Unmanaged<CFString>?>.size)
        var nameAddr = AudioObjectPropertyAddress(
            mSelector: kAudioObjectPropertyName,
            mScope: kAudioObjectPropertyScopeGlobal,
            mElement: kAudioObjectPropertyElementMain)
        let st = AudioObjectGetPropertyData(id, &nameAddr, 0, nil, &nameSize, &nameRef)
        let name = (st == noErr) ? (nameRef?.takeRetainedValue() as String? ?? "(unknown)") : "(unknown)"
        result.append((id, name))
    }
    return result
}

func findDevice(_ substr: String) -> AudioDeviceID? {
    let want = substr.lowercased()
    return outputDevices().first(where: { $0.name.lowercased().contains(want) })?.id
}

// ---- argv ----

let args = Array(CommandLine.arguments.dropFirst())

if args.first == "--list" {
    for d in outputDevices() { out("\(d.name)") }
    exit(0)
}

var deviceSubstr: String? = nil
var filePath: String? = nil
var serveMode = false
var i = 0
while i < args.count {
    if args[i] == "--device", i + 1 < args.count {
        deviceSubstr = args[i + 1]; i += 2
    } else if args[i] == "--serve" {
        serveMode = true; i += 1
    } else {
        filePath = args[i]; i += 1
    }
}

// ---- engine targeting the chosen device ----

let engine = AVAudioEngine()
func bindDevice() {
    guard let sub = deviceSubstr else { return }
    if let devID = findDevice(sub) {
        if let unit = engine.outputNode.audioUnit {
            var dev = devID
            let st = AudioUnitSetProperty(unit,
                kAudioOutputUnitProperty_CurrentDevice,
                kAudioUnitScope_Global, 0,
                &dev, UInt32(MemoryLayout<AudioDeviceID>.size))
            if st != noErr { log("warning: could not set output device (status \(st)); using default") }
        }
    } else {
        log("warning: no output device matching '\(sub)'; using default")
    }
}
bindDevice()

let player = AVAudioPlayerNode()
engine.attach(player)
// A standard 44.1k stereo float format for the mixer connection (resampled per file).
let mixFormat = AVAudioFormat(standardFormatWithSampleRate: 44100, channels: 2)!
engine.connect(player, to: engine.mainMixerNode, format: mixFormat)

func playOneShot(_ path: String) {
    let url = URL(fileURLWithPath: path)
    guard FileManager.default.fileExists(atPath: path) else { log("file not found: \(path)"); return }
    do {
        let file = try AVAudioFile(forReading: url)
        let done = DispatchSemaphore(value: 0)
        player.scheduleFile(file, at: nil, completionCallbackType: .dataPlayedBack) { _ in done.signal() }
        if !player.isPlaying { player.play() }
        let lengthSeconds = Double(file.length) / file.processingFormat.sampleRate
        _ = done.wait(timeout: DispatchTime.now() + lengthSeconds + 3.0)
    } catch {
        log("playback failed for \(path): \(error)")
    }
}

if serveMode {
    do {
        try engine.start()
        log("[play] serve mode ready; reading file paths on stdin")
    } catch {
        log("[play] engine start failed: \(error)")
        exit(3)
    }
    // Engine stays running (keeps A2DP warm). Schedule each requested file.
    while let line = readLine(strippingNewline: true) {
        let p = line.trimmingCharacters(in: .whitespaces)
        if p.isEmpty { continue }
        if p == "__quit__" { break }
        let url = URL(fileURLWithPath: p)
        guard FileManager.default.fileExists(atPath: p) else { log("missing: \(p)"); continue }
        do {
            let file = try AVAudioFile(forReading: url)
            player.scheduleFile(file, at: nil, completionCallbackType: .dataConsumed, completionHandler: nil)
            if !player.isPlaying { player.play() }
        } catch {
            log("schedule failed for \(p): \(error)")
        }
    }
    engine.stop()
    exit(0)
}

// one-shot mode
guard let path = filePath else {
    log("Usage: ditoo-play [--device NAME] <audiofile> | --serve | --list")
    exit(1)
}
do {
    try engine.start()
} catch {
    log("engine start failed: \(error)")
    exit(3)
}
playOneShot(path)
engine.stop()
