# This file downloads all of F.3d (the third reporter of federal appellate cases) from case.law
import json, os, subprocess


def get_volumes():
    with open("VolumesMetadata.json", "r") as f:
        vols = json.load(f)
    for vol in vols:
        print(vol["volume_number"])
        if os.path.exists(vol["volume_number"]):
            # Check if it's a directory
            assert os.path.isdir(vol["volume_number"])
        else:
            # If it doesn't exist, create the directory
            os.makedirs(vol["volume_number"])

        os.chdir(vol["volume_number"])

        if not os.path.exists("CasesMetadata.json"):
            subprocess.run(["wget",
                            "https://static.case.law/f3d/"+vol["volume_number"]+"/CasesMetadata.json"],
                           check=True)

        with open("CasesMetadata.json", "r") as cases_f:
            cases = json.load(cases_f)

        for case in cases:
            if not os.path.exists(case["file_name"]+".json"):
                print(vol["volume_number"] + "/" + case["file_name"])
                subprocess.run(["wget",
                                "https://static.case.law/f3d/" + vol["volume_number"] +
                                "/cases/" + case["file_name"] + ".json"],
                               check=True)
            else:
                print("Already have", vol["volume_number"] , case["file_name"])


        os.chdir("..")


if __name__ == "__main__":
    get_volumes()