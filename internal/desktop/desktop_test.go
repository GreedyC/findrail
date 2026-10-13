package desktop

import (
	"net"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"testing"
)

func TestCanonicalDirectoryHasOneOwnerAndRecordCannotCauseUnverifiedReuse(t *testing.T) {
	dir := t.TempDir()
	alias := filepath.Join(t.TempDir(), "alias")
	if err := os.Symlink(dir, alias); err != nil {
		t.Skipf("symlink unavailable: %v", err)
	}
	owner, err := Acquire(dir)
	if err != nil {
		t.Fatal(err)
	}
	defer owner.Close()
	if _, err = Acquire(alias); err != ErrOwned {
		t.Fatalf("alias acquired second owner: %v", err)
	}
	if _, err = ReadRecord(dir); err == nil {
		t.Fatal("missing record unexpectedly accepted")
	}
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	defer listener.Close()
	record, err := NewRecord(owner.DataDir, "http://"+listener.Addr().String())
	if err != nil {
		t.Fatal(err)
	}
	if err = owner.Publish(record); err != nil {
		t.Fatal(err)
	}
	loaded, err := ReadRecord(alias)
	if err != nil {
		t.Fatal(err)
	}
	if Verify(loaded) {
		t.Fatal("unrelated listener verified as Findrail")
	}
	bad := record
	bad.Nonce = "short"
	if err = owner.Publish(bad); err == nil {
		t.Fatal("invalid nonce published")
	}
}

func TestIdentityRequiresExactPrivateRecord(t *testing.T) {
	s := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{"product":"Findrail","data_dir":"/tmp/data","nonce":"secret"}`))
	}))
	defer s.Close()
	if Verify(Record{Version: 1, DataDir: "/tmp/data", URL: s.URL, Nonce: "different"}) {
		t.Fatal("identity accepted a mismatched nonce")
	}
}
