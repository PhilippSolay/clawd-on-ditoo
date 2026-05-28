// DitooBridge — a thin RFCOMM/SPP bridge for the Divoom Ditoo family on macOS.
//
// Modes:
//   ditoo-bridge list                       Print paired Divoom devices (name, address)
//   ditoo-bridge services <mac>             Run SDP query; print services + their RFCOMM channel numbers.
//   ditoo-bridge send <mac> [--channel N]   Open RFCOMM channel; forward length-prefixed stdin frames to device.
//   ditoo-bridge listen <mac> [--channel N] Open RFCOMM channel; print inbound bytes as hex+timestamp lines.
//
// stdin framing for `send`: each outbound packet is preceded by a 2-byte little-endian
// length header. Length 0 (`00 00`) cleanly closes the channel. We ack each frame on
// stdout with a single line: `OK` or `ERR <ioreturn>`.
//
// stdout format for `listen`: one line per inbound chunk:  `<unix_ms> <hex_bytes>`

import Foundation
import IOBluetooth

let stderr = FileHandle.standardError
let stdoutHandle = FileHandle.standardOutput
let stdinHandle = FileHandle.standardInput

func log(_ s: String) {
    if let d = (s + "\n").data(using: .utf8) { stderr.write(d) }
}
func reply(_ s: String) {
    if let d = (s + "\n").data(using: .utf8) { stdoutHandle.write(d) }
}

// Identify a paired device as "Divoom-ish" by checking its name.
func isDivoom(_ name: String?) -> Bool {
    guard let n = name?.lowercased() else { return false }
    return n.contains("divoom") || n.contains("ditoo") || n.contains("pixoo") || n.contains("timoo") || n.contains("tivoo")
}

func runList() -> Int32 {
    guard let paired = IOBluetoothDevice.pairedDevices() as? [IOBluetoothDevice] else {
        log("Could not enumerate paired devices.")
        return 2
    }
    for d in paired {
        let name = d.name ?? "(no name)"
        let addr = d.addressString ?? "??"
        if isDivoom(name) {
            print("\(addr)\t\(name)")
        }
    }
    return 0
}

final class RFCOMMDelegate: NSObject, IOBluetoothRFCOMMChannelDelegate {
    var openSem = DispatchSemaphore(value: 0)
    var openStatus: IOReturn = kIOReturnError
    var closed = false

    func rfcommChannelOpenComplete(_ rfcommChannel: IOBluetoothRFCOMMChannel!, status error: IOReturn) {
        openStatus = error
        openSem.signal()
    }
    func rfcommChannelClosed(_ rfcommChannel: IOBluetoothRFCOMMChannel!) {
        closed = true
        log("[bridge] channel closed")
        // Exit the run loop so main can wind down.
        CFRunLoopStop(CFRunLoopGetMain())
    }
    var onInboundBytes: ((Data) -> Void)?

    func rfcommChannelData(_ rfcommChannel: IOBluetoothRFCOMMChannel!,
                           data dataPointer: UnsafeMutableRawPointer!,
                           length dataLength: Int) {
        if let cb = onInboundBytes, dataLength > 0, let p = dataPointer {
            let buf = UnsafeRawBufferPointer(start: p, count: dataLength)
            cb(Data(buf))
        }
    }
}

func runSend(mac: String, channelID: UInt8) -> Int32 {
    guard let device = IOBluetoothDevice(addressString: mac) else {
        log("Unknown device: \(mac)")
        return 2
    }
    if !device.isPaired() {
        log("Device \(mac) is not paired. Pair it via System Settings -> Bluetooth first.")
        return 3
    }

    let delegate = RFCOMMDelegate()
    // Retry: a recently-closed connection can leave the RFCOMM channel busy for a
    // few seconds, and the device may be momentarily unavailable. Back off and retry.
    var ch: IOBluetoothRFCOMMChannel? = nil
    var lastResult: IOReturn = kIOReturnError
    for attempt in 1...5 {
        var channel: IOBluetoothRFCOMMChannel?
        lastResult = device.openRFCOMMChannelSync(&channel,
                                                  withChannelID: BluetoothRFCOMMChannelID(channelID),
                                                  delegate: delegate)
        if lastResult == kIOReturnSuccess, channel != nil {
            ch = channel
            break
        }
        log("[bridge] open attempt \(attempt)/5 failed: \(String(format: "0x%x", lastResult)); retrying in 1.5s")
        Thread.sleep(forTimeInterval: 1.5)
    }
    guard let ch = ch else {
        log("openRFCOMMChannelSync failed after retries: \(String(format: "0x%x", lastResult)). "
            + "Another process may be holding the channel — kill stray ditoo-bridge processes.")
        return 4
    }
    log("[bridge] connected to \(mac) channel \(channelID)")

    // Read stdin in a background thread; the run loop on the main thread drives IOBluetooth callbacks.
    let stdinQueue = DispatchQueue(label: "stdin-reader")
    stdinQueue.async {
        while !delegate.closed {
            guard let hdr = try? stdinHandle.read(upToCount: 2), hdr.count == 2 else {
                log("[bridge] stdin EOF")
                break
            }
            let len = Int(hdr[0]) | (Int(hdr[1]) << 8)
            if len == 0 {
                log("[bridge] zero-length frame; closing")
                break
            }
            var got = Data()
            while got.count < len {
                let want = len - got.count
                guard let chunk = try? stdinHandle.read(upToCount: want), !chunk.isEmpty else {
                    log("[bridge] short read (\(got.count)/\(len)); closing")
                    return
                }
                got.append(chunk)
            }
            // writeSync wants a mutable raw pointer. Copy into a mutable buffer.
            var bytes = [UInt8](got)
            let ret = bytes.withUnsafeMutableBufferPointer { buf -> IOReturn in
                guard let base = buf.baseAddress else { return kIOReturnNoMemory }
                return ch.writeSync(base, length: UInt16(buf.count))
            }
            if ret == kIOReturnSuccess {
                reply("OK")
            } else {
                reply("ERR \(String(format: "0x%x", ret))")
            }
        }
        DispatchQueue.main.async {
            ch.close()
            CFRunLoopStop(CFRunLoopGetMain())
        }
    }

    CFRunLoopRun()
    log("[bridge] exiting")
    return 0
}

final class SDPDelegate: NSObject {
    var done = false
    var status: IOReturn = kIOReturnError
    @objc func sdpQueryComplete(_ device: IOBluetoothDevice, status: IOReturn) {
        self.status = status
        self.done = true
        CFRunLoopStop(CFRunLoopGetMain())
    }
}

func runServices(mac: String) -> Int32 {
    guard let device = IOBluetoothDevice(addressString: mac) else {
        log("Unknown device: \(mac)")
        return 2
    }

    // Kick off a fresh SDP query and pump the run loop until it completes (or times out).
    let delegate = SDPDelegate()
    let q = device.performSDPQuery(delegate)
    if q != kIOReturnSuccess {
        log("performSDPQuery returned \(String(format: "0x%x", q)); falling back to cached records")
    } else {
        let deadline = Date().addingTimeInterval(8)
        while !delegate.done && Date() < deadline {
            RunLoop.current.run(mode: .default, before: Date().addingTimeInterval(0.25))
        }
        if !delegate.done {
            log("SDP query timed out; using whatever records are cached")
        }
    }

    guard let services = device.services as? [IOBluetoothSDPServiceRecord], !services.isEmpty else {
        log("No SDP service records available for \(mac).")
        return 3
    }

    print("Found \(services.count) SDP service record(s) on \(mac):")
    var rfcommChannels: [(UInt8, String)] = []
    for rec in services {
        let name = rec.getServiceName() ?? "(unnamed)"
        var channelID: BluetoothRFCOMMChannelID = 0
        let hasRFCOMM = rec.getRFCOMMChannelID(&channelID) == kIOReturnSuccess
        if hasRFCOMM {
            print("  RFCOMM ch \(channelID)\t\(name)")
            rfcommChannels.append((UInt8(channelID), name))
        } else {
            print("  (no rfcomm)\t\(name)")
        }
    }
    print("")
    if rfcommChannels.isEmpty {
        print("No RFCOMM/SPP channels found. Pixel control over serial is unlikely on this device.")
    } else {
        print("Candidate channels for pixel control (try with `send ... --channel N`):")
        for (ch, name) in rfcommChannels {
            print("  --channel \(ch)   (\(name))")
        }
    }
    return 0
}

func runListen(mac: String, channelID: UInt8) -> Int32 {
    guard let device = IOBluetoothDevice(addressString: mac) else {
        log("Unknown device: \(mac)")
        return 2
    }
    if !device.isPaired() {
        log("Device \(mac) is not paired. Pair it via System Settings -> Bluetooth first.")
        return 3
    }

    let delegate = RFCOMMDelegate()
    delegate.onInboundBytes = { data in
        let ms = Int64(Date().timeIntervalSince1970 * 1000)
        let hex = data.map { String(format: "%02x", $0) }.joined()
        if let line = "\(ms) \(hex)\n".data(using: .utf8) {
            stdoutHandle.write(line)
        }
    }

    var channel: IOBluetoothRFCOMMChannel?
    let openResult = device.openRFCOMMChannelSync(&channel,
                                                  withChannelID: BluetoothRFCOMMChannelID(channelID),
                                                  delegate: delegate)
    guard openResult == kIOReturnSuccess, channel != nil else {
        log("openRFCOMMChannelSync failed: \(String(format: "0x%x", openResult))")
        return 4
    }
    log("[bridge] LISTEN mode connected to \(mac) channel \(channelID); press buttons on the device")

    // Hold the run loop until the channel closes or SIGINT.
    signal(SIGINT) { _ in
        CFRunLoopStop(CFRunLoopGetMain())
    }
    CFRunLoopRun()
    log("[bridge] listen exiting")
    return 0
}

// ---------- argv ----------

let args = Array(CommandLine.arguments.dropFirst())
if args.isEmpty {
    log("Usage: ditoo-bridge list | services <mac> | send <mac> [--channel N] | listen <mac> [--channel N]")
    exit(1)
}

switch args[0] {
case "list":
    exit(runList())
case "services":
    guard args.count >= 2 else { log("services needs <mac>"); exit(1) }
    exit(runServices(mac: args[1]))
case "send":
    guard args.count >= 2 else { log("send needs <mac>"); exit(1) }
    let mac = args[1]
    var channel: UInt8 = 1
    if let i = args.firstIndex(of: "--channel"), i + 1 < args.count, let n = UInt8(args[i + 1]) {
        channel = n
    }
    exit(runSend(mac: mac, channelID: channel))
case "listen":
    guard args.count >= 2 else { log("listen needs <mac>"); exit(1) }
    let mac = args[1]
    var channel: UInt8 = 1
    if let i = args.firstIndex(of: "--channel"), i + 1 < args.count, let n = UInt8(args[i + 1]) {
        channel = n
    }
    exit(runListen(mac: mac, channelID: channel))
default:
    log("Unknown command: \(args[0])")
    exit(1)
}
