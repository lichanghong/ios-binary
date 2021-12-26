//
//  main.swift
//  SourcePodspecToBinary
//
//  Created by lch on 18/08/2021.
//

import Foundation



func handleJson(path: String, source: String, output: String) {
    let data = FileManager.default.contents(atPath: path)
    if let data = data {
        var jsonDic = try! JSONSerialization.jsonObject(with: data, options: JSONSerialization.ReadingOptions.mutableContainers) as! Dictionary<String, Any>
        let moduleName = jsonDic["name"]!
        // MARK: 设置组件source
        jsonDic["source"] = ["http":source]
        
        let dependencies: Dictionary<String, Any> = [:] // 依赖
        var vendored_librarys: Array<String> = [] // vendored_library
        var vendored_frameworks: Array<String> = [] // vendored_frameworks
        var frameworks: Array<String> = [] // frameworks
        var libraries: Array<String> = []  //libraries
        var resources: Array<String> = []  //resources
        var sourcefiles: Array<String> = [] //sourcefiles
        // MARK: 处理subspec
        if let subspecs = jsonDic["subspecs"] as? Array<Dictionary<String, Any>> {
            /// 处理subspec中的source_files和vendored_library
            let newSubspecs = __configNewSubspecs(moduleName: "lib\(moduleName).a", allSubSpec: subspecs)
            
            /// 修改后的subspec赋值给json
            jsonDic["subspecs"] = newSubspecs
        }
        
        /// dependencies
        if var allDepends = jsonDic["dependencies"] as? Dictionary<String, Any> {
            dependencies.forEach { (key, value) in
                allDepends[key] = value
            }
            var finalDepends: Dictionary<String, Any> = [:]
            allDepends.forEach { (key, value) in
                if key.contains("/"), let newKey = key.components(separatedBy: "/").first {
                    finalDepends[newKey] = value
                } else {
                    finalDepends[key] = value
                }
            }
            jsonDic["dependencies"] = finalDepends
        } else {
            jsonDic["dependencies"] = dependencies
        }
        
        /// 处理ios标签里的lib和framework
        if var ios = jsonDic["ios"] as? Dictionary<String, Any> {
            if let vlibraries = ios["vendored_libraries"] as? Array<String> {
                vendored_librarys.append(contentsOf: vlibraries)
            } else if let vlibraries = ios["vendored_libraries"] as? String {
                vendored_librarys.append(vlibraries)
            }
            vendored_librarys.append("lib\(moduleName).a")
            ios.merge(["vendored_libraries":vendored_librarys]) { (_, new) in
                return new
            }
            
            if let vframeworks = ios["vendored_frameworks"] as? Array<String> {
                vendored_frameworks.append(contentsOf: vframeworks)
            } else if let vframeworks = ios["vendored_frameworks"] as? String {
                vendored_frameworks.append(vframeworks)
            }
            ios.merge(["vendored_frameworks":vendored_frameworks]) { (_, new) in
                return new
            }
            jsonDic["ios"] = ios
        } else {
            vendored_librarys.append("lib\(moduleName).a")
            jsonDic["ios"] = [
                "vendored_libraries": vendored_librarys,
                "vendored_frameworks": vendored_frameworks
            ]
        }
        
        /// frameworks标签
        if var allframeworks = jsonDic["frameworks"] as? Array<String> {
            allframeworks.append(contentsOf: frameworks)
            jsonDic["frameworks"] = allframeworks
        } else if let framework = jsonDic["frameworks"] as? String {
            frameworks.append(framework)
            jsonDic["frameworks"] = frameworks
        } else {
            jsonDic["frameworks"] = frameworks
        }
        
        /// libraries标签
        if var alllibraries = jsonDic["libraries"] as? Array<String> {
            alllibraries.append(contentsOf: libraries)
            jsonDic["libraries"] = alllibraries
        } else if let lib = jsonDic["libraries"] as? String {
            libraries.append(lib)
            jsonDic["libraries"] = libraries
        } else {
            jsonDic["libraries"] = libraries
        }
        
        /// resources
        if var allresources = jsonDic["resources"] as? Array<String> {
            allresources.append(contentsOf: resources)
            jsonDic["resources"] = allresources
        } else if let res = jsonDic["resources"] as? String {
            resources.append(res)
            jsonDic["resources"] = resources
        } else {
            jsonDic["resources"] = resources
        }
        
        /// source_files
        if var allsourcefiles = jsonDic["source_files"] as? Array<String> {
            allsourcefiles = allsourcefiles.map {
                return __handleSourceFile(source: $0)
            }
            allsourcefiles.append(contentsOf: sourcefiles)
            jsonDic["source_files"] = allsourcefiles
        } else if let source = jsonDic["source_files"] as? String {
            sourcefiles.append(__handleSourceFile(source: source))
            jsonDic["source_files"] = sourcefiles
        } else {
            jsonDic["source_files"] = sourcefiles
        }
                
        // MARK: 重新写入文件
        let data = try? JSONSerialization.data(withJSONObject: jsonDic, options: JSONSerialization.WritingOptions.prettyPrinted)
        var str = String(data: data!, encoding: String.Encoding.utf8)
        str = str?.replacingOccurrences(of: "\\/", with: "/")
        try! str!.write(toFile: output, atomically: true, encoding: String.Encoding.utf8)
    }
}

func __configNewSubspecs(moduleName: String, allSubSpec: Array<Dictionary<String, Any>>) -> Array<Dictionary<String, Any>> {
    var newSubspecs: Array<Dictionary<String, Any>> = []
    for i in 0..<allSubSpec.count {
        var subspec: Dictionary<String, Any> = allSubSpec[i]
        
        // 处理source_files
        var source_files: Array<String> = []
        if let subSourceFiles = subspec["source_files"] as? Array<String> {
            subSourceFiles.forEach { (item) in
                let newItem = __handleSourceFile(source: item)
                source_files.append(newItem)
            }
        } else if let subSourceFile = subspec["source_files"] as? String {
            let newItem = __handleSourceFile(source: subSourceFile)
            source_files.append(newItem)
        }
        subspec["source_files"] = source_files
        
        // 处理vendored_libraries
        var ios: Dictionary<String, Any> = [:]
        let vendored_libraries: Array<String> = [moduleName]
        if let subIos = subspec["ios"] as? Dictionary<String, Any> {
            ios = subIos
        }
        ios["vendored_libraries"] = vendored_libraries
        subspec["ios"] = ios
        
        newSubspecs.append(subspec)
    }
    return newSubspecs
}

func __handleSourceFile(source: String) -> String {
    var source_subs = source.split(separator: "/")
    if source_subs.last!.contains(".") || source_subs.last!.contains("*") {
        source_subs = source_subs.dropLast()
    }
    var result = ""
    if source_subs.count > 0 {
        result = source_subs.joined(separator: "/")+"/*.{h}"
    } else {
        result = "*.{h}"
    }
    return result
}


let path = CommandLine.arguments[1]
let source = CommandLine.arguments[2]
let output = CommandLine.arguments[3]
print(path)
print(source)
print(output)


handleJson(path: path, source: source, output: output)
 
