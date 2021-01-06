package checks

import (
	"bytes"
	"context"
	"fmt"

	"github.com/docker/docker/api/types"
	"github.com/docker/docker/api/types/filters"
	"github.com/docker/docker/client"
	"github.com/docker/docker/pkg/stdcopy"
)

func ComposeCheck(projName string) (Check, error) {
	c := Check{}

	ctx := context.Background()
	cli, err := client.NewClientWithOpts(client.FromEnv, client.WithAPIVersionNegotiation())
	if err != nil {
		return c, err
	}

	opts := types.ContainerListOptions{
		All: true,
		Filters: filters.NewArgs(
			filters.KeyValuePair{
				Key:   "label",
				Value: "com.docker.compose.project=" + projName}),
	}
	containers, err := cli.ContainerList(ctx, opts)
	if err != nil {
		return c, err
	}

	c.Status.Val = OK
	for _, container := range containers {
		if len(c.Status.Msg) > 0 {
			c.Status.Msg += ", "
		}
		c.Status.Msg += fmt.Sprintf("%s(%s)", container.Labels["com.docker.compose.service"], container.State)
		if container.State != "running" {
			c.Status.Val = ERROR
		}
	}

	c.GetLog = func() (string, error) {
		log := ""
		logOpts := types.ContainerLogsOptions{
			ShowStdout: true,
			ShowStderr: true,
			Tail:       "20",
		}
		for _, container := range containers {
			fmt.Println(container.ID)
			r, err := cli.ContainerLogs(ctx, container.ID, logOpts)
			if err != nil {
				fmt.Println("DY HErE")
				return log, err
			}
			defer r.Close()
			log += "## " + container.Labels["com.docker.compose.service"] + " ---------------\n"
			var b bytes.Buffer
			if _, err := stdcopy.StdCopy(&b, &b, r); err != nil {
				fmt.Println("Dy HErE")
				return log, err
			}
			log += b.String() + "\n"
		}
		return log, nil
	}
	return c, nil
}
