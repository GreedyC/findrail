package sqlite_test

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"testing"

	"github.com/Lephiziel/findrail/internal/connectors/filesystem"
	"github.com/Lephiziel/findrail/internal/ingest"
	"github.com/Lephiziel/findrail/internal/search"
	"github.com/Lephiziel/findrail/internal/store/sqlite"
)

// Setup and indexing are deliberately outside the timer; the benchmark reports
// only the production store Search call and its allocations.
func BenchmarkSearch(b *testing.B) {
	for _, count := range []int{100, 1000} {
		b.Run(fmt.Sprintf("documents_%d", count), func(b *testing.B) {
			root := b.TempDir()
			for i := 0; i < count; i++ {
				text := fmt.Sprintf("synthetic commonmark document %d", i)
				if i%97 == 0 {
					text += " raretoken"
				}
				if err := os.WriteFile(filepath.Join(root, fmt.Sprintf("doc-%06d.md", i)), []byte(text), 0600); err != nil {
					b.Fatal(err)
				}
			}
			dir := filepath.Join(b.TempDir(), "index")
			store, err := sqlite.Open(context.Background(), dir)
			if err != nil {
				b.Fatal(err)
			}
			defer store.Close()
			conn, err := filesystem.New(root, 1<<20, dir)
			if err != nil {
				b.Fatal(err)
			}
			if _, err := ingest.Run(context.Background(), store, conn); err != nil {
				b.Fatal(err)
			}
			request := search.Request{Query: "commonmark", Limit: 20}
			b.ReportAllocs()
			b.ResetTimer()
			for i := 0; i < b.N; i++ {
				if _, err := store.Search(context.Background(), request); err != nil {
					b.Fatal(err)
				}
			}
		})
	}
}
