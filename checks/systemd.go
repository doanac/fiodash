package checks

import (
	"fmt"
	"io/ioutil"

	"github.com/coreos/go-systemd/v22/dbus"
	"github.com/coreos/go-systemd/v22/sdjournal"
)

type ServiceState struct {
	UnitFileState string
	ActiveState   string
	SubState      string
}

func (ss ServiceState) Running() bool {
	return ss.ActiveState == "active" && ss.SubState == "running"
}

func (ss ServiceState) String() string {
	return fmt.Sprintf("%s / %s (%s)", ss.UnitFileState, ss.ActiveState, ss.SubState)
}

func getServiceState(unit string) (ServiceState, error) {
	conn, err := dbus.NewSystemConnection()
	state := ServiceState{}
	if err != nil {
		return state, err
	}
	defer conn.Close()
	props, err := conn.GetUnitProperties(unit + ".service")
	if err != nil {
		return state, err
	}
	state.UnitFileState = props["UnitFileState"].(string)
	state.ActiveState = props["ActiveState"].(string)
	state.SubState = props["SubState"].(string)
	return state, nil
}

func getServiceLogs(unit string, numLines int) (string, error) {
	r, err := sdjournal.NewJournalReader(sdjournal.JournalReaderConfig{
		NumFromTail: uint64(numLines),
		Matches: []sdjournal.Match{
			{
				Field: sdjournal.SD_JOURNAL_FIELD_SYSTEMD_UNIT,
				Value: unit + ".service",
			},
		},
	})
	if err != nil {
		return "", err
	}

	b, err := ioutil.ReadAll(r)
	if err != nil {
		return "", err
	}
	return string(b), nil
}

func DoSystemDCheck(unit string) (Check, error) {
	c := Check{}
	ss, err := getServiceState(unit)
	if err != nil {
		return c, err
	}
	c.Status.Msg = ss.String()
	if ss.Running() {
		c.Status.Val = OK
	} else {
		c.Status.Val = ERROR
	}
	c.GetLog = func() (string, error) {
		return getServiceLogs(unit, 20)
	}
	return c, nil
}
