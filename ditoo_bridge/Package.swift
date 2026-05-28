// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "DitooBridge",
    platforms: [.macOS(.v13)],
    targets: [
        .executableTarget(
            name: "DitooBridge",
            path: "Sources/DitooBridge"
        )
    ]
)
