package sqlite

import (
	"context"
	"database/sql"
	"os"
	"path/filepath"
	"testing"

	"github.com/Lephiziel/findrail/internal/connectors/filesystem"
	"github.com/Lephiziel/findrail/internal/ingest"
	"github.com/Lephiziel/findrail/internal/search"
)

func TestPersistentCollectionSnapshotRevisionAndDocumentRemoval(t *testing.T) {
	ctx := context.Background()
	data := t.TempDir()
	root := t.TempDir()
	doc := filepath.Join(root, "note.md")
	if e := os.WriteFile(doc, []byte("alpha beta gamma"), 0600); e != nil {
		t.Fatal(e)
	}
	s, e := Open(ctx, data)
	if e != nil {
		t.Fatal(e)
	}
	defer s.Close()
	conn, e := filesystem.New(root, 1<<20)
	if e != nil {
		t.Fatal(e)
	}
	if _, e = ingest.Run(ctx, s, conn); e != nil {
		t.Fatal(e)
	}
	// Resolve the indexed ID without trusting metadata from a client.
	var id string
	if e = s.readers.QueryRowContext(ctx, "SELECT id FROM documents LIMIT 1").Scan(&id); e != nil {
		t.Fatal(e)
	}
	c, e := s.CreateCollection(ctx, "Research")
	if e != nil {
		t.Fatal(e)
	}
	pinned, e := s.PinCollectionEntry(ctx, c.ID, c.Revision, id, 0, "alpha beta", false)
	if e != nil {
		t.Fatal(e)
	}
	if pinned.Revision != 2 || len(pinned.Entries) != 1 {
		t.Fatalf("pinned=%+v", pinned)
	}
	entry := pinned.Entries[0]
	entry.Note = "note"
	saved, e := s.UpdateCollection(ctx, c.ID, pinned.Revision, "Renamed", []CollectionEntry{entry})
	if e != nil {
		t.Fatal(e)
	}
	if saved.Revision != 3 || saved.Entries[0].Note != "note" {
		t.Fatalf("saved=%+v", saved)
	}
	if _, e = s.UpdateCollection(ctx, c.ID, pinned.Revision, "Stale", nil); e != ErrCollectionConflict {
		t.Fatalf("stale edit=%v", e)
	}
	forged := saved.Entries[0]
	forged.Evidence.URI = "file:///forged"
	if _, e = s.UpdateCollection(ctx, c.ID, saved.Revision, "Forged", []CollectionEntry{forged}); e == nil {
		t.Fatal("accepted forged evidence snapshot")
	}
	oldHash := saved.Entries[0].Evidence.ContentHash
	if e = os.WriteFile(doc, []byte("changed indexed version"), 0600); e != nil {
		t.Fatal(e)
	}
	conn, e = filesystem.New(root, 1<<20)
	if e != nil {
		t.Fatal(e)
	}
	if _, e = ingest.Run(ctx, s, conn); e != nil {
		t.Fatal(e)
	}
	historical, e := s.LoadCollection(ctx, c.ID)
	if e != nil {
		t.Fatal(e)
	}
	if historical.Entries[0].Evidence.ContentHash != oldHash || historical.Entries[0].Evidence.Text != "alpha beta gamma" {
		t.Fatalf("refresh rewrote historical snapshot: %+v", historical.Entries[0])
	}
	if e = os.Remove(doc); e != nil {
		t.Fatal(e)
	}
	conn, e = filesystem.New(root, 1<<20)
	if e != nil {
		t.Fatal(e)
	}
	if _, e = ingest.Run(ctx, s, conn); e != nil {
		t.Fatal(e)
	}
	after, e := s.LoadCollection(ctx, c.ID)
	if e != nil {
		t.Fatal(e)
	}
	if len(after.Entries) != 0 || after.Title != "Renamed" {
		t.Fatalf("removed document did not cascade: %+v", after)
	}
	if e = s.DeleteCollection(ctx, c.ID, after.Revision); e != nil {
		t.Fatal(e)
	}
}

func TestForgetAndReaddDoesNotResurrectCollectionEntry(t *testing.T) {
	ctx := context.Background()
	s, e := Open(ctx, t.TempDir())
	if e != nil {
		t.Fatal(e)
	}
	defer s.Close()
	root := t.TempDir()
	if e = os.WriteFile(filepath.Join(root, "note.md"), []byte("forget lifecycle evidence"), 0600); e != nil {
		t.Fatal(e)
	}
	conn, e := filesystem.New(root, 1<<20)
	if e != nil {
		t.Fatal(e)
	}
	if _, e = ingest.Run(ctx, s, conn); e != nil {
		t.Fatal(e)
	}
	var id string
	if e = s.readers.QueryRowContext(ctx, "SELECT id FROM documents LIMIT 1").Scan(&id); e != nil {
		t.Fatal(e)
	}
	c, e := s.CreateCollection(ctx, "Keep name")
	if e != nil {
		t.Fatal(e)
	}
	if _, e = s.PinCollectionEntry(ctx, c.ID, c.Revision, id, 0, "forget lifecycle", false); e != nil {
		t.Fatal(e)
	}
	if e = s.ForgetSource(ctx, conn.Source().ID); e != nil {
		t.Fatal(e)
	}
	after, e := s.LoadCollection(ctx, c.ID)
	if e != nil || len(after.Entries) != 0 || after.Title != "Keep name" {
		t.Fatalf("forget result=%+v err=%v", after, e)
	}
	conn, e = filesystem.New(root, 1<<20)
	if e != nil {
		t.Fatal(e)
	}
	if _, e = ingest.Run(ctx, s, conn); e != nil {
		t.Fatal(e)
	}
	after, e = s.LoadCollection(ctx, c.ID)
	if e != nil || len(after.Entries) != 0 {
		t.Fatalf("re-add restored forgotten entry: %+v %v", after, e)
	}
}

func TestCollectionSaveIsAtomicForNewPinsAndOrdering(t *testing.T) {
	ctx := context.Background()
	s, e := Open(ctx, t.TempDir())
	if e != nil {
		t.Fatal(e)
	}
	defer s.Close()
	root := t.TempDir()
	_ = os.WriteFile(filepath.Join(root, "a.md"), []byte("first saved excerpt and second saved excerpt"), 0600)
	conn, e := filesystem.New(root, 1<<20)
	if e != nil {
		t.Fatal(e)
	}
	if _, e = ingest.Run(ctx, s, conn); e != nil {
		t.Fatal(e)
	}
	var id string
	if e = s.readers.QueryRowContext(ctx, "SELECT id FROM documents LIMIT 1").Scan(&id); e != nil {
		t.Fatal(e)
	}
	c, e := s.CreateCollection(ctx, "Batch")
	if e != nil {
		t.Fatal(e)
	}
	bad := []CollectionEdit{{Note: "first", DocumentID: id, Excerpt: "first saved excerpt"}, {Note: "bad", DocumentID: "missing", Excerpt: "missing"}}
	if _, e = s.SaveCollection(ctx, c.ID, c.Revision, "Batch", bad); e == nil {
		t.Fatal("partial save unexpectedly succeeded")
	}
	after, e := s.LoadCollection(ctx, c.ID)
	if e != nil || after.Revision != c.Revision || len(after.Entries) != 0 {
		t.Fatalf("failed batch committed partially: %+v %v", after, e)
	}
	good := []CollectionEdit{{Note: "first", DocumentID: id, Excerpt: "first saved excerpt"}, {Note: "second", DocumentID: id, Excerpt: "second saved excerpt"}}
	saved, e := s.SaveCollection(ctx, c.ID, c.Revision, "Renamed", good)
	if e != nil {
		t.Fatal(e)
	}
	if len(saved.Entries) != 2 || saved.Entries[0].Note != "first" || saved.Revision != 2 {
		t.Fatalf("saved=%+v", saved)
	}
	if _, e = s.SaveCollection(ctx, c.ID, c.Revision, "stale", good); e != ErrCollectionConflict {
		t.Fatalf("stale save=%v", e)
	}
}

func TestSchemaSixMigrationAndRollback(t *testing.T) {
	ctx := context.Background()
	dir := t.TempDir()
	s, e := Open(ctx, dir)
	if e != nil {
		t.Fatal(e)
	}
	root := t.TempDir()
	if e = os.WriteFile(filepath.Join(root, "schema6.md"), []byte("schema six retained search data"), 0600); e != nil {
		t.Fatal(e)
	}
	conn, e := filesystem.New(root, 1<<20)
	if e != nil {
		t.Fatal(e)
	}
	if _, e = ingest.Run(ctx, s, conn); e != nil {
		t.Fatal(e)
	}
	if _, e = s.db.ExecContext(ctx, "CREATE TABLE sources_copy AS SELECT * FROM sources; DROP TABLE evidence_collection_entries; DROP TABLE evidence_collections; PRAGMA user_version=6"); e != nil {
		t.Fatal(e)
	}
	s.Close()
	s, e = Open(ctx, dir)
	if e != nil {
		t.Fatal(e)
	}
	var version int
	if e = s.db.QueryRowContext(ctx, "PRAGMA user_version").Scan(&version); e != nil || version != 7 {
		t.Fatalf("version=%d err=%v", version, e)
	}
	if sources, err := s.Sources(ctx); err != nil || len(sources) != 1 || sources[0].Documents != 1 {
		t.Fatalf("sources after migration=%+v err=%v", sources, err)
	}
	if result, err := s.Search(ctx, search.Request{Query: "schema six retained", Limit: 5}); err != nil || result.Total != 1 {
		t.Fatalf("search after migration=%+v err=%v", result, err)
	}
	s.Close()
	broken := t.TempDir()
	s, e = Open(ctx, broken)
	if e != nil {
		t.Fatal(e)
	}
	if _, e = s.db.ExecContext(ctx, "DROP TABLE evidence_collection_entries; DROP TABLE evidence_collections; CREATE TABLE evidence_collections(id TEXT); PRAGMA user_version=6"); e != nil {
		t.Fatal(e)
	}
	s.Close()
	if _, e = Open(ctx, broken); e == nil {
		t.Fatal("expected migration failure")
	}
	db, e := sql.Open("sqlite", filepath.Join(broken, "findrail.db"))
	if e != nil {
		t.Fatal(e)
	}
	defer db.Close()
	if e = db.QueryRow("PRAGMA user_version").Scan(&version); e != nil || version != 6 {
		t.Fatalf("failed migration changed version=%d err=%v", version, e)
	}
}
