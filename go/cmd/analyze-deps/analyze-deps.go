// analyze-deps analyzes dependencies for TinyTroupe Go modules
package main

import (
	"fmt"
	"go/ast"
	"go/parser"
	"go/token"
	"log"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

// Dependency represents a module dependency
type Dependency struct {
	Package string
	Module  string
	Used    []string // Functions, types, etc. used from this dependency
}

// ModuleInfo holds information about a Go module
type ModuleInfo struct {
	Name         string
	Path         string
	Dependencies []Dependency
	Exports      []string // Public functions, types, etc.
}

func main() {
	if len(os.Args) < 2 {
		fmt.Println("Usage: go run cmd/analyze-deps/analyze-deps.go <pkg-directory>")
		fmt.Println("Example: go run cmd/analyze-deps/analyze-deps.go pkg/agent")
		os.Exit(1)
	}

	pkgDir := os.Args[1]

	fmt.Printf("Analyzing dependencies for: %s\n", pkgDir)
	fmt.Println("=====================================")

	moduleInfo, err := analyzeModule(pkgDir)
	if err != nil {
		log.Fatalf("Error analyzing module: %v", err)
	}

	printModuleInfo(moduleInfo)
}

func analyzeModule(pkgDir string) (*ModuleInfo, error) {
	info := &ModuleInfo{
		Name: filepath.Base(pkgDir),
		Path: pkgDir,
	}

	// Parse all Go files in the directory
	fset := token.NewFileSet()
	pkgs, err := parser.ParseDir(fset, pkgDir, nil, parser.ParseComments)
	if err != nil {
		return nil, fmt.Errorf("failed to parse directory: %w", err)
	}

	depMap := make(map[string]*Dependency)
	exportSet := make(map[string]bool)

	for _, pkg := range pkgs {
		for _, file := range pkg.Files {
			// Analyze imports
			for _, imp := range file.Imports {
				importPath := strings.Trim(imp.Path.Value, "\"")

				// Skip standard library and current module
				if !strings.Contains(importPath, ".") {
					continue
				}
				if strings.HasPrefix(importPath, "github.com/microsoft/TinyTroupe/go/") {
					module := extractModuleName(importPath)
					if _, exists := depMap[importPath]; !exists {
						depMap[importPath] = &Dependency{
							Package: importPath,
							Module:  module,
							Used:    []string{},
						}
					}
				}
			}

			// Analyze exported identifiers
			ast.Inspect(file, func(n ast.Node) bool {
				switch node := n.(type) {
				case *ast.FuncDecl:
					if node.Name.IsExported() {
						exportSet[node.Name.Name] = true
					}
				case *ast.TypeSpec:
					if node.Name.IsExported() {
						exportSet[node.Name.Name] = true
					}
				case *ast.ValueSpec:
					for _, name := range node.Names {
						if name.IsExported() {
							exportSet[name.Name] = true
						}
					}
				}
				return true
			})
		}
	}

	// Convert maps to slices
	for _, dep := range depMap {
		info.Dependencies = append(info.Dependencies, *dep)
	}

	for export := range exportSet {
		info.Exports = append(info.Exports, export)
	}

	// Sort for consistent output
	sort.Slice(info.Dependencies, func(i, j int) bool {
		return info.Dependencies[i].Package < info.Dependencies[j].Package
	})
	sort.Strings(info.Exports)

	return info, nil
}

func extractModuleName(importPath string) string {
	parts := strings.Split(importPath, "/")
	if len(parts) >= 2 {
		return parts[len(parts)-1]
	}
	return importPath
}

func printModuleInfo(info *ModuleInfo) {
	fmt.Printf("📦 Module: %s\n", info.Name)
	fmt.Printf("📍 Path: %s\n", info.Path)
	fmt.Println()

	if len(info.Dependencies) > 0 {
		fmt.Println("🔗 Internal Dependencies:")
		for _, dep := range info.Dependencies {
			fmt.Printf("  • %s (%s)\n", dep.Module, dep.Package)
		}
		fmt.Println()
	} else {
		fmt.Println("🔗 No internal dependencies found")
		fmt.Println()
	}

	if len(info.Exports) > 0 {
		fmt.Println("📤 Exported Identifiers:")
		for _, export := range info.Exports {
			fmt.Printf("  • %s\n", export)
		}
		fmt.Println()
	} else {
		fmt.Println("📤 No exported identifiers found")
		fmt.Println()
	}

	// Migration recommendations
	fmt.Println("💡 Migration Recommendations:")
	if len(info.Dependencies) == 0 {
		fmt.Println("  ✅ This module has no internal dependencies - good for early migration")
	} else {
		fmt.Println("  ⚠️  This module has dependencies - consider migration order:")
		for _, dep := range info.Dependencies {
			fmt.Printf("     - Ensure %s is migrated first\n", dep.Module)
		}
	}

	if len(info.Exports) > 0 {
		fmt.Printf("  📋 %d public interfaces to implement\n", len(info.Exports))
	}
}
