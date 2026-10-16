package cli

import (
	"bytes"
	"context"
	"database/sql"
	"encoding/json"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
	"testing"
	"time"

	"github.com/Lephiziel/findrail/internal/store/sqlite"
	"github.com/Lephiziel/findrail/pkg/connector"
	sdkmcp "github.com/modelcontextprotocol/go-sdk/mcp"
)

// Launch the compiled CLI using exactly the generated argv, rather than a
// separately constructed protocol fixture or a test-binary substitute.
func TestGeneratedMCPConfigSDKJourney(t *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 90*time.Second)
	defer cancel()
	name := "findrail 測試 cli"
	goName := "go"
	if runtime.GOOS == "windows" {
		name += ".exe"
		goName += ".exe"
	}
	// Native package verification supplies the freshly extracted candidate.
	// Ordinary source tests retain the Unicode/space-path build below.
	binary := os.Getenv("FINDRAIL_MCP_TEST_BINARY")
	if binary == "" {
		binary = filepath.Join(t.TempDir(), name)
		build := exec.CommandContext(ctx, filepath.Join(runtime.GOROOT(), "bin", goName), "build", "-o", binary, "../../cmd/findrail")
		if output, err := build.CombinedOutput(); err != nil {
			t.Fatalf("build CLI: %v\n%s", err, output)
		}
	} else {
		resolved, err := filepath.Abs(binary)
		if err != nil {
			t.Fatal(err)
		}
		binary = resolved
		if info, err := os.Stat(binary); err != nil || !info.Mode().IsRegular() {
			t.Fatalf("packaged MCP executable is unavailable: %s (%v)", binary, err)
		}
	}
	t.Logf("MCP SDK journey executable: %s", binary)
	dir := filepath.Join(t.TempDir(), "index 測試 spaces")
	store, err := sqlite.Open(ctx, dir)
	if err != nil {
		t.Fatal(err)
	}
	for _, id := range []string{"源-β", "denied"} {
		scan, err := store.BeginScan(ctx, connector.Source{ID: id, Kind: "filesystem", Name: "synthetic"})
		if err != nil {
			t.Fatal(err)
		}
		_, err = scan.Upsert(ctx, connector.Document{ID: "doc-" + id, SourceID: id, Title: "guide.pdf", Path: "guide.pdf", URI: "file:///synthetic/guide.pdf", MediaType: "application/pdf", Content: "introduction\nscopedneedle page two", Hash: "synthetic-v1", Pages: []connector.Page{{Number: 1, Text: "introduction"}, {Number: 2, Text: "scopedneedle page two"}}})
		if err != nil {
			_ = scan.Rollback()
			t.Fatal(err)
		}
		body := strings.Repeat("合成😀 filler ", 4500) + " latepassageanchor " + strings.Repeat("ending ", 100)
		if _, err := scan.Upsert(ctx, connector.Document{ID: "note-" + id, SourceID: id, Title: "late.md", Path: "late.md", URI: "file:///synthetic/late.md", MediaType: "text/markdown", Content: body, Hash: "synthetic-late-v1"}); err != nil {
			_ = scan.Rollback()
			t.Fatal(err)
		}
		if _, err := scan.Commit(ctx); err != nil {
			t.Fatal(err)
		}
	}
	if err := store.Close(); err != nil {
		t.Fatal(err)
	}
	before, err := os.ReadFile(filepath.Join(dir, "findrail.db"))
	if err != nil {
		t.Fatal(err)
	}
	for _, client := range []string{"vscode", "claude-desktop"} {
		for _, protocol := range []string{"2026-07-28", "2025-11-25"} {
			t.Run(client+"/"+protocol, func(t *testing.T) {
				var generated, stderr bytes.Buffer
				generate := exec.CommandContext(ctx, binary, "mcp-config", "--client", client, "--data-dir", dir, "--source", "源-β")
				generate.Stdout, generate.Stderr = &generated, &stderr
				if err := generate.Run(); err != nil || stderr.Len() != 0 {
					t.Fatalf("generate config: %v stderr=%s", err, &stderr)
				}
				var config generatedMCPConfig
				if err := json.Unmarshal(generated.Bytes(), &config); err != nil {
					t.Fatal(err)
				}
				server := config.MCPServers["findrail"]
				if server.Command != binary || !equalStrings(server.Args, []string{"mcp", "--data-dir", dir, "--source", "源-β"}) {
					t.Fatalf("unexpected generated scope: %+v", server)
				}
				command := exec.CommandContext(ctx, server.Command, server.Args...)
				command.Stderr = &stderr
				transport := &sdkmcp.CommandTransport{Command: command, TerminateDuration: 10 * time.Second}
				session, err := sdkmcp.NewClient(&sdkmcp.Implementation{Name: "config-test", Version: "test"}, nil).Connect(ctx, transport, &sdkmcp.ClientSessionOptions{ProtocolVersion: protocol})
				if err != nil {
					t.Fatalf("connect: %v stderr=%s", err, &stderr)
				}
				t.Cleanup(func() { _ = session.Close() })
				if session.InitializeResult().ProtocolVersion != protocol {
					t.Fatal("protocol negotiation changed")
				}
				tools, err := session.ListTools(ctx, nil)
				if err != nil || len(tools.Tools) != 3 {
					t.Fatalf("list tools: %v %+v", err, tools)
				}
				call := func(name string, args map[string]any, wantError bool) map[string]any {
					t.Helper()
					result, err := session.CallTool(ctx, &sdkmcp.CallToolParams{Name: name, Arguments: args})
					if err != nil || result.IsError != wantError {
						t.Fatalf("%s error=%v result=%+v", name, err, result)
					}
					encoded, err := json.Marshal(result.StructuredContent)
					if err != nil {
						t.Fatal(err)
					}
					var fields map[string]any
					if err := json.Unmarshal(encoded, &fields); err != nil {
						t.Fatal(err)
					}
					return fields
				}
				sources := call("findrail_list_sources", map[string]any{}, false)["sources"].([]any)
				if len(sources) != 1 || sources[0].(map[string]any)["id"] != "源-β" {
					t.Fatalf("source scope leaked: %+v", sources)
				}
				found := call("findrail_search", map[string]any{"source_id": "源-β", "query": "scopedneedle"}, false)
				if found["total"] != float64(1) || found["results"].([]any)[0].(map[string]any)["id"] != "doc-源-β" {
					t.Fatalf("search scope: %+v", found)
				}
				late := call("findrail_search", map[string]any{"source_id": "源-β", "query": "latepassageanchor"}, false)
				lateHit := late["results"].([]any)[0].(map[string]any)
				identity := lateHit["original_identity"].(string)
				passage := call("findrail_get_evidence", map[string]any{"source_id": "源-β", "document_id": "note-源-β", "query": "latepassageanchor", "original_identity": identity}, false)
				if passage["match_kind"] != "literal_body" || !strings.Contains(passage["text"].(string), "latepassageanchor") || passage["text_start_char"].(float64) < 8000 {
					t.Fatalf("late passage anchor: %+v", passage)
				}
				continued := call("findrail_get_evidence", map[string]any{"source_id": "源-β", "document_id": "note-源-β", "start_char": 10000, "original_identity": identity}, false)
				if continued["text_start_char"] != float64(10000) {
					t.Fatalf("manual continuation: %+v", continued)
				}
				evidence := call("findrail_get_evidence", map[string]any{"source_id": "源-β", "document_id": "doc-源-β", "page": 2}, false)
				if evidence["page"] != float64(2) || evidence["page_count"] != float64(2) || evidence["text"] != "scopedneedle page two" {
					t.Fatalf("PDF page attribution: %+v", evidence)
				}
				call("findrail_search", map[string]any{"source_id": "denied", "query": "scopedneedle"}, true)
				call("findrail_get_evidence", map[string]any{"source_id": "denied", "document_id": "doc-denied"}, true)
				call("findrail_get_evidence", map[string]any{"source_id": "源-β", "document_id": "doc-denied"}, true)
				closed := time.Now()
				if err := session.Close(); err != nil {
					t.Fatal(err)
				}
				if time.Since(closed) >= 10*time.Second || command.ProcessState == nil || !command.ProcessState.Success() {
					t.Fatalf("child did not exit cleanly on EOF: %v stderr=%s", command.ProcessState, &stderr)
				}
			})
		}
	}
	after, err := os.ReadFile(filepath.Join(dir, "findrail.db"))
	if err != nil || !bytes.Equal(before, after) {
		t.Fatalf("config/protocol journey modified the index: %v", err)
	}
}

func TestMCPConfigRejectsUnsupportedSchemaWithoutMigration(t *testing.T) {
	dir := mcpTestIndex(t)
	db, err := sql.Open("sqlite", filepath.Join(dir, "findrail.db"))
	if err != nil {
		t.Fatal(err)
	}
	if _, err := db.Exec("PRAGMA user_version=9999"); err != nil {
		t.Fatal(err)
	}
	if err := db.Close(); err != nil {
		t.Fatal(err)
	}
	before, err := os.ReadFile(filepath.Join(dir, "findrail.db"))
	if err != nil {
		t.Fatal(err)
	}
	var out bytes.Buffer
	err = runMCPConfig(context.Background(), []string{"--client", "vscode", "--data-dir", dir, "--source", "allowed"}, &out, &bytes.Buffer{})
	if err == nil || !strings.Contains(err.Error(), "unsupported index schema") || out.Len() != 0 {
		t.Fatalf("unsupported schema: %v stdout=%s", err, &out)
	}
	after, err := os.ReadFile(filepath.Join(dir, "findrail.db"))
	if err != nil || !bytes.Equal(before, after) {
		t.Fatalf("failed generation changed the index: %v", err)
	}
}
