package checks

import "os"

func fileExists(path string) bool {
	_, err := os.Stat(path)
	return err == nil
}

func AkliteCheck() (Check, error) {
	if !fileExists("/var/sota/client.pem") {
		// Device hasn't be registered
		c, err := DoSystemDCheck("lmp-device-auto-register")
		if err != nil {
			return Check{}, err
		}
		c.Status.Msg = "Device not registered. lmp-device-auto-register " + c.Status.Msg
		return c, nil
	}

	return DoSystemDCheck("aktualizr-lite")
}
