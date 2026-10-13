package main

import (
	"context"
	"errors"
	"fmt"
	"os"
	"os/signal"
	"syscall"

	"github.com/Lephiziel/findrail/internal/cli"
)

var version = "dev"

func main() {
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()
	args := append([]string{"desktop"}, os.Args[1:]...)
	if err := cli.Run(ctx, args, os.Stdout, os.Stderr, version); err != nil {
		fmt.Fprintln(os.Stderr, "findrail-desktop:", err)
		var exit interface{ ExitCode() int }
		if errors.As(err, &exit) {
			os.Exit(exit.ExitCode())
		}
		os.Exit(1)
	}
}
