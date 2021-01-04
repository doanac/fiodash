package main

import (
	"fmt"
	"log"
	"os"

	"github.com/urfave/cli/v2"

	"github.com/foundriesio/fiodash/internal"
)

func main() {
	app := &cli.App{
		Name:  "fiodash",
		Usage: "A tool to explain the status of a device",
		Commands: []*cli.Command{
			{
				Name:  "version",
				Usage: "Display version of this command",
				Action: func(c *cli.Context) error {
					fmt.Println(internal.Commit)
					return nil
				},
			},
		},
	}

	err := app.Run(os.Args)
	if err != nil {
		log.Fatal(err)
	}
}
