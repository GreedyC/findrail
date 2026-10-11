package cli

import (
	"context"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"strings"

	"github.com/Lephiziel/findrail/internal/connectors/filesystem"
)

type pathsFlag []string

func (p *pathsFlag) String() string     { return strings.Join(*p, ",") }
func (p *pathsFlag) Set(v string) error { *p = append(*p, v); return nil }

func runExplainPath(ctx context.Context, args []string, out, stderr io.Writer) error {
	if len(args) > 0 && (args[0] == "--help" || args[0] == "-h") {
		_, err := fmt.Fprintln(out, "Usage: findrail explain-path ROOT --path RELATIVE [--path RELATIVE ...] [--json] [--show-rule]")
		return err
	}
	if len(args) == 0 {
		return errors.New("explain-path requires ROOT and --path")
	}
	root := args[0]
	opts := append([]string(nil), args[1:]...)
	fs := flag.NewFlagSet("explain-path", flag.ContinueOnError)
	fs.SetOutput(stderr)
	var paths pathsFlag
	fs.Var(&paths, "path", "root-relative POSIX path (repeatable)")
	jsonOut := fs.Bool("json", false, "output versioned JSON")
	show := fs.Bool("show-rule", false, "include matched rule text")
	if err := fs.Parse(opts); err != nil {
		if errors.Is(err, flag.ErrHelp) {
			return nil
		}
		return err
	}
	if fs.NArg() != 0 || len(paths) == 0 || len(paths) > 100 {
		return errors.New("explain-path requires ROOT and 1–100 --path values")
	}
	type row struct {
		Path        string `json:"path"`
		Status      string `json:"status"`
		Reason      string `json:"reason,omitempty"`
		Fingerprint string `json:"policy_fingerprint,omitempty"`
		Rule        string `json:"rule,omitempty"`
		Line        int    `json:"line,omitempty"`
		Ancestor    string `json:"ancestor,omitempty"`
	}
	rows := make([]row, 0, len(paths))
	present := false
	for _, path := range paths {
		d, err := filesystem.Explain(ctx, root, path, *show)
		if err != nil {
			return err
		}
		present = present || d.Fingerprint != ""
		status, reason := d.Reason, ""
		if strings.HasPrefix(status, "excluded_builtin:") {
			status, reason = "excluded_builtin", strings.TrimPrefix(status, "excluded_builtin:")
		}
		rows = append(rows, row{Path: path, Status: status, Reason: reason, Fingerprint: d.Fingerprint, Rule: d.Rule, Line: d.Line, Ancestor: d.Ancestor})
	}
	if *jsonOut {
		b, err := json.Marshal(struct {
			Version       int   `json:"version"`
			PolicyPresent bool  `json:"policy_present"`
			Results       []row `json:"results"`
		}{1, present, rows})
		if err != nil {
			return err
		}
		if len(b) > 256<<10 {
			return errors.New("explanation output limit exceeded")
		}
		_, err = fmt.Fprintln(out, string(b))
		return err
	}
	if present {
		if _, err := fmt.Fprintf(out, "Policy: present (%s)\n", rows[0].Fingerprint); err != nil {
			return err
		}
	} else {
		if _, err := fmt.Fprintln(out, "Policy: absent"); err != nil {
			return err
		}
	}
	for _, r := range rows {
		if _, err := fmt.Fprintf(out, "%s: %s", r.Path, r.Status); err != nil {
			return err
		}
		if r.Line > 0 {
			if _, err := fmt.Fprintf(out, " (line %d", r.Line); err != nil {
				return err
			}
			if r.Rule != "" {
				if _, err := fmt.Fprintf(out, ": %s", safe(r.Rule)); err != nil {
					return err
				}
			}
			if _, err := fmt.Fprint(out, ")"); err != nil {
				return err
			}
		}
		if r.Ancestor != "" && r.Ancestor != r.Path {
			if _, err := fmt.Fprintf(out, " (%s)", r.Ancestor); err != nil {
				return err
			}
		}
		if _, err := fmt.Fprintln(out); err != nil {
			return err
		}
	}
	return nil
}
