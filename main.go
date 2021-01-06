package main

import (
	"fmt"
	"log"
	"os"
	"text/tabwriter"

	"github.com/urfave/cli/v2"

	"github.com/foundriesio/fiodash/checks"
	"github.com/foundriesio/fiodash/internal"
	"github.com/foundriesio/fiodash/server"
)

func runChecks() error {
	w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
	e := checks.Iterate(func(name string, checkFunc checks.CheckFunc) error {
		ss, err := checkFunc()
		if err != nil {
			fmt.Fprintf(w, "%s\tERROR\t%s\n", name, err)
		} else {
			fmt.Fprintf(w, "%s\t%s\t%s\n", name, ss.Status.Val, ss.Status.Msg)
		}
		return nil
	})
	w.Flush()
	return e
}

func checkDetails(name string) error {
	check, ok := checks.GetCheck(name)
	if !ok {
		return fmt.Errorf("ERROR: No such check: %s", name)
	}
	ss, err := check()
	if err != nil {
		return err
	}
	fmt.Println("Name:  ", name)
	fmt.Println("Status:", ss.Status.Val, ss.Status.Msg)
	log, err := ss.GetLog()
	fmt.Println("Logs:")
	fmt.Println(log)
	return err
}

func main() {
	var checkName string
	var port int

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
			{
				Name: "checks",
				Flags: []cli.Flag{
					&cli.StringFlag{
						Name:        "check-naame",
						Aliases:     []string{"n"},
						Usage:       "Run a single check",
						Destination: &checkName,
					},
				},
				Action: func(c *cli.Context) error {
					if len(checkName) == 0 {
						return runChecks()
					} else {
						return checkDetails(checkName)
					}
				},
			},
			{
				Name: "serve",
				Flags: []cli.Flag{
					&cli.IntFlag{
						Name:        "port",
						Aliases:     []string{"p"},
						Usage:       "Port to use",
						Value:       80,
						Destination: &port,
					},
				},
				Action: func(c *cli.Context) error {
					return server.Serve(port)
				},
			},
		},
	}

	err := app.Run(os.Args)
	if err != nil {
		log.Fatal(err)
	}
}
