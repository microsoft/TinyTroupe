// compare-apis compares API compatibility between TinyTroupe modules
package main

import (
	"fmt"
	"go/ast"
	"go/parser"
	"go/token"
	"log"
	"os"
	"sort"
	"strings"
)

// APIInfo represents API information for a module
type APIInfo struct {
	Module    string
	Functions []FunctionInfo
	Types     []TypeInfo
	Constants []ConstantInfo
}

// FunctionInfo represents a function signature
type FunctionInfo struct {
	Name       string
	Params     []string
	Returns    []string
	IsExported bool
}

// TypeInfo represents a type definition
type TypeInfo struct {
	Name       string
	Kind       string // struct, interface, alias, etc.
	IsExported bool
}

// ConstantInfo represents a constant definition
type ConstantInfo struct {
	Name       string
	Type       string
	IsExported bool
}

func main() {
	if len(os.Args) < 3 {
		fmt.Println("Usage: go run cmd/compare-apis/compare-apis.go <old-module-path> <new-module-path>")
		fmt.Println("Example: go run cmd/compare-apis/compare-apis.go pkg/agent pkg/agent_new")
		os.Exit(1)
	}

	oldPath := os.Args[1]
	newPath := os.Args[2]

	fmt.Printf("Comparing APIs: %s vs %s\n", oldPath, newPath)
	fmt.Println("=====================================")

	oldAPI, err := extractAPI(oldPath)
	if err != nil {
		log.Fatalf("Error analyzing old module: %v", err)
	}

	newAPI, err := extractAPI(newPath)
	if err != nil {
		log.Fatalf("Error analyzing new module: %v", err)
	}

	compareAPIs(oldAPI, newAPI)
}

func extractAPI(pkgPath string) (*APIInfo, error) {
	info := &APIInfo{
		Module: pkgPath,
	}

	fset := token.NewFileSet()
	pkgs, err := parser.ParseDir(fset, pkgPath, nil, parser.ParseComments)
	if err != nil {
		return nil, fmt.Errorf("failed to parse directory: %w", err)
	}

	for _, pkg := range pkgs {
		for _, file := range pkg.Files {
			ast.Inspect(file, func(n ast.Node) bool {
				switch node := n.(type) {
				case *ast.FuncDecl:
					if node.Name != nil {
						funcInfo := extractFunctionInfo(node)
						info.Functions = append(info.Functions, funcInfo)
					}
				case *ast.TypeSpec:
					if node.Name != nil {
						typeInfo := extractTypeInfo(node)
						info.Types = append(info.Types, typeInfo)
					}
				case *ast.ValueSpec:
					for _, name := range node.Names {
						constInfo := ConstantInfo{
							Name:       name.Name,
							IsExported: name.IsExported(),
						}
						if node.Type != nil {
							constInfo.Type = fmt.Sprintf("%v", node.Type)
						}
						info.Constants = append(info.Constants, constInfo)
					}
				}
				return true
			})
		}
	}

	// Sort for consistent comparison
	sort.Slice(info.Functions, func(i, j int) bool {
		return info.Functions[i].Name < info.Functions[j].Name
	})
	sort.Slice(info.Types, func(i, j int) bool {
		return info.Types[i].Name < info.Types[j].Name
	})
	sort.Slice(info.Constants, func(i, j int) bool {
		return info.Constants[i].Name < info.Constants[j].Name
	})

	return info, nil
}

func extractFunctionInfo(funcDecl *ast.FuncDecl) FunctionInfo {
	info := FunctionInfo{
		Name:       funcDecl.Name.Name,
		IsExported: funcDecl.Name.IsExported(),
	}

	// Extract parameters
	if funcDecl.Type.Params != nil {
		for _, param := range funcDecl.Type.Params.List {
			paramType := fmt.Sprintf("%v", param.Type)
			for _, name := range param.Names {
				info.Params = append(info.Params, fmt.Sprintf("%s %s", name.Name, paramType))
			}
			// Handle unnamed parameters
			if len(param.Names) == 0 {
				info.Params = append(info.Params, paramType)
			}
		}
	}

	// Extract return types
	if funcDecl.Type.Results != nil {
		for _, result := range funcDecl.Type.Results.List {
			resultType := fmt.Sprintf("%v", result.Type)
			info.Returns = append(info.Returns, resultType)
		}
	}

	return info
}

func extractTypeInfo(typeSpec *ast.TypeSpec) TypeInfo {
	info := TypeInfo{
		Name:       typeSpec.Name.Name,
		IsExported: typeSpec.Name.IsExported(),
	}

	switch typeSpec.Type.(type) {
	case *ast.StructType:
		info.Kind = "struct"
	case *ast.InterfaceType:
		info.Kind = "interface"
	default:
		info.Kind = "alias"
	}

	return info
}

func compareAPIs(oldAPI, newAPI *APIInfo) {
	fmt.Printf("🔍 Analyzing API compatibility\n\n")

	// Compare functions
	compareFunctions(oldAPI.Functions, newAPI.Functions)

	// Compare types
	compareTypes(oldAPI.Types, newAPI.Types)

	// Compare constants
	compareConstants(oldAPI.Constants, newAPI.Constants)

	// Summary
	fmt.Println("📊 Summary:")
	fmt.Printf("  Old API: %d functions, %d types, %d constants\n",
		len(oldAPI.Functions), len(oldAPI.Types), len(oldAPI.Constants))
	fmt.Printf("  New API: %d functions, %d types, %d constants\n",
		len(newAPI.Functions), len(newAPI.Types), len(newAPI.Constants))
}

func compareFunctions(oldFuncs, newFuncs []FunctionInfo) {
	fmt.Println("🔧 Functions:")

	oldMap := make(map[string]FunctionInfo)
	newMap := make(map[string]FunctionInfo)

	for _, f := range oldFuncs {
		if f.IsExported {
			oldMap[f.Name] = f
		}
	}

	for _, f := range newFuncs {
		if f.IsExported {
			newMap[f.Name] = f
		}
	}

	// Check for missing functions
	for name := range oldMap {
		if _, exists := newMap[name]; !exists {
			fmt.Printf("  ❌ Missing function: %s\n", name)
		}
	}

	// Check for new functions
	for name := range newMap {
		if _, exists := oldMap[name]; !exists {
			fmt.Printf("  ✅ New function: %s\n", name)
		}
	}

	// Check for signature changes
	for name, oldFunc := range oldMap {
		if newFunc, exists := newMap[name]; exists {
			if !equalStringSlices(oldFunc.Params, newFunc.Params) ||
				!equalStringSlices(oldFunc.Returns, newFunc.Returns) {
				fmt.Printf("  ⚠️  Changed signature: %s\n", name)
				fmt.Printf("     Old: (%s) -> (%s)\n",
					strings.Join(oldFunc.Params, ", "),
					strings.Join(oldFunc.Returns, ", "))
				fmt.Printf("     New: (%s) -> (%s)\n",
					strings.Join(newFunc.Params, ", "),
					strings.Join(newFunc.Returns, ", "))
			}
		}
	}

	fmt.Println()
}

func compareTypes(oldTypes, newTypes []TypeInfo) {
	fmt.Println("📋 Types:")

	oldMap := make(map[string]TypeInfo)
	newMap := make(map[string]TypeInfo)

	for _, t := range oldTypes {
		if t.IsExported {
			oldMap[t.Name] = t
		}
	}

	for _, t := range newTypes {
		if t.IsExported {
			newMap[t.Name] = t
		}
	}

	// Check for missing types
	for name := range oldMap {
		if _, exists := newMap[name]; !exists {
			fmt.Printf("  ❌ Missing type: %s\n", name)
		}
	}

	// Check for new types
	for name := range newMap {
		if _, exists := oldMap[name]; !exists {
			fmt.Printf("  ✅ New type: %s\n", name)
		}
	}

	// Check for kind changes
	for name, oldType := range oldMap {
		if newType, exists := newMap[name]; exists {
			if oldType.Kind != newType.Kind {
				fmt.Printf("  ⚠️  Changed kind: %s (%s -> %s)\n",
					name, oldType.Kind, newType.Kind)
			}
		}
	}

	fmt.Println()
}

func compareConstants(oldConstants, newConstants []ConstantInfo) {
	fmt.Println("📌 Constants:")

	oldMap := make(map[string]ConstantInfo)
	newMap := make(map[string]ConstantInfo)

	for _, c := range oldConstants {
		if c.IsExported {
			oldMap[c.Name] = c
		}
	}

	for _, c := range newConstants {
		if c.IsExported {
			newMap[c.Name] = c
		}
	}

	// Check for missing constants
	for name := range oldMap {
		if _, exists := newMap[name]; !exists {
			fmt.Printf("  ❌ Missing constant: %s\n", name)
		}
	}

	// Check for new constants
	for name := range newMap {
		if _, exists := oldMap[name]; !exists {
			fmt.Printf("  ✅ New constant: %s\n", name)
		}
	}

	fmt.Println()
}

func equalStringSlices(a, b []string) bool {
	if len(a) != len(b) {
		return false
	}
	for i := range a {
		if a[i] != b[i] {
			return false
		}
	}
	return true
}
