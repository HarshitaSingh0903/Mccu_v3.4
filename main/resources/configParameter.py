import json


def createConfigFile(output_filename):
    data = {
        "flagCheck": {"minimum": 0, "maximum": 1},
        "sysTemp": {"minimum": -10, "maximum": 60},
        "osuRoll": {"minimum": -30, "maximum": 30},
        "osuPitch": {"minimum": -15, "maximum": 15},
        "osuYaw": {"minimum": 0, "maximum": 360},
        "beaconPower": {"minimum": -80, "maximum": -60},
        "tarAz": {"minimum": 0, "maximum": 360},
        "tarEl": {"minimum": -20, "maximum": 90},
        "tarPol": {"minimum": -45, "maximum": 45},
        "currEl": {"minimum": -20, "maximum": 90},
        "currCl": {"minimum": -30, "maximum": 30},
        "currAz": {"minimum": 0, "maximum": 360},
        "currPol": {"minimum": 45, "maximum": 45},
        "motorElCurr": {"minimum": 0.5, "maximum": 2.0},
        "motorClCurr": {"minimum": 0.5, "maximum": 2.0},
        "motorAzCurr": {"minimum": 0.5, "maximum": 1.0},
        "motorPolCurr": {"minimum": 0.5, "maximum": 2.0},
        "bucCurr": {"minimum": 0.5, "maximum": 2.0},
        "opticalFibreCurr": {"minimum": 0.5, "maximum": 2.0},
        "slscCurr": {"minimum": 5.0, "maximum": 10.0},
        "totalCurr": {"minimum": 10.0, "maximum": 15.0},
    }

    # Write the dictionary to a JSON file
    with open(output_filename, "w") as json_file:
        json.dump(data, json_file, indent=4)

    print(f"JSON data written to {output_filename}")


def editConfigFile(tempMinValue, tempMaxValue,rollMinValue, rollMaxValue, pitchMinValue, pitchMaxValue, yawMinValue, yawMaxValue,
                   beaconMinValue,beaconMaxValue, tarAzMinValue, tarAzMaxValue, tarElMinValue, tarElMaxValue, tarPolMinValue,
                   tarPolMaxValue,currElMinValue, currElMaxValue, currxElMinValue, currxElMaxValue, currAzMinValue,currAzMaxValue,
                    currPolMinValue,currPolMaxValue, mCurrElMinValue,mCurrElMaxValue,mCurrxElMinValue, mCurrxElMaxValue,mCurrAzMinValue, mCurrAzMaxValue,
                    mCurrPolMinValue,  mCurrPolMaxValue, bucCurrMinValue, bucCurrMaxValue, ofcCurrMinValue, ofcCurrMaxValue,
                    slscCurrMinValue,  slscCurrMaxValue, totalCurrMinValue , totalCurrMaxValue ):
    data = {
        "flagCheck": {"minimum": 0, "maximum": 1},
        "sysTemp": {"minimum": float(tempMinValue), "maximum": float(tempMaxValue)},
        "osuRoll": {"minimum": float(rollMinValue), "maximum": float(rollMaxValue)},
        "osuPitch": {"minimum": float(pitchMinValue), "maximum": float(pitchMaxValue)},
        "osuYaw": {"minimum": float(yawMinValue), "maximum": float(yawMaxValue)},
        "beaconPower": {"minimum": float(beaconMinValue), "maximum": float(beaconMaxValue)},
        "tarAz": {"minimum": float(tarAzMinValue), "maximum": float(tarAzMaxValue)},
        "tarEl": {"minimum": float(tarElMinValue), "maximum": float(tarElMaxValue)},
        "tarPol": {"minimum": float(tarPolMinValue), "maximum": float(tarPolMaxValue)},
        "currEl": {"minimum": float(currElMinValue), "maximum": float(currElMaxValue)},
        "currCl": {"minimum": float(currxElMinValue), "maximum": float(currxElMaxValue)},
        "currAz": {"minimum": float(currAzMinValue), "maximum": float(currAzMaxValue)},
        "currPol": {"minimum": float(currPolMinValue), "maximum": float(currPolMaxValue)},
        "motorElCurr": { "minimum": float(mCurrElMinValue), "maximum": float(mCurrElMaxValue), },
        "motorClCurr": { "minimum": float(mCurrxElMinValue), "maximum": float(mCurrxElMaxValue), },
        "motorAzCurr": { "minimum": float(mCurrAzMinValue), "maximum": float(mCurrAzMaxValue), },
        "motorPolCurr": { "minimum": float(mCurrPolMinValue), "maximum": float(mCurrPolMaxValue), },
        "bucCurr": { "minimum": float(bucCurrMinValue), "maximum": float(bucCurrMaxValue), },
        "opticalFibreCurr": { "minimum": float(ofcCurrMinValue),  "maximum": float(ofcCurrMaxValue), },
        "slscCurr": { "minimum": float(slscCurrMinValue),  "maximum": float(slscCurrMaxValue), },
        "totalCurr": { "minimum": float(totalCurrMinValue), "maximum": float(totalCurrMaxValue), },
    }

    # Write the dictionary to a JSON file
    output_filename = "mccuConfig.json"  # Provide the desired output filename
    with open(output_filename, "w") as json_file:
        json.dump(data, json_file, indent=4)

    print(f"JSON data written to {output_filename}")
