import os
import re
import time
import json 
import shutil
import glob 
import warnings

# import numpy as np
# import nibabel as nib
# import pynrrd
# import matplotlib.pyplot as plt

# import pydicom
# import pydicom_seg
import SimpleITK as sitk

from pathlib import Path
from pydicom.uid import generate_uid

# from kaapana.workflows.dags.example.files.segmentation_processing import find_code_meaning

# def get_tags_from_meta(meta_path):
#     meta = json.load(meta_path)


def make_out_dir(series_uid, dataset, case, segmentation=False, human_readable=False):
    # operator_output = "/data/output" 
    batch_output = os.path.join('/', os.environ['WORKFLOW_DIR'], os.environ['BATCH_NAME']) #, os.environ['OPERATOR_OUT_DIR'])


    os.environ["OPERATOR_OUT_DIR"] if os.environ[ "OPERATOR_OUT_DIR"] is not None else "/data/output"
    
    if not os.path.exists(batch_output):
        os.mkdir(batch_output)
    if human_readable:
        case_dir = Path(batch_output)/dataset/str(case).split(".")[0]
    else:
        case_dir = Path(f"{batch_output}/{series_uid}/{os.environ['OPERATOR_OUT_DIR']}")
    dicom_dir =  case_dir/ 'dicoms' # Dicom Directory
    dicom_dir.mkdir(exist_ok=True, parents=True)
    
    if segmentation:
        nii_segmentation_dir = case_dir / 'segmentations'
        nii_segmentation_dir.mkdir(exist_ok=True, parents=True)
    
    return case_dir

# def get_seg_info():
#     # case 1 seg info is dict in meta_data


class Nifti2DcmConverter:
    """ Converter for itk compatible file formats as nifti and nrrd to dicom. Since these formats do 
    not include all necessary meta information, it is possible to provide additional meta information 
    on a 'per study' basis. (See __call__(self, ...))
    """
    def __init__(self):
        self.parser = Parser()
    
    def __call__(self, path, meta_data=None):
        """ Run the converter on a path with the following directory structure:

        path
        |----study1
        |    | meta_data.json
        |    | series1.nii.gz
        |    | series1_seg.nii.gz
        |    | series2.nii.gz
        |    | series2_seg.nii.gz
        |    | ...
        |
        |----study2
        |    | meta_data.json
        |    | series1.nii.gz
        |    | series1_seg.nii.gz
        |    | series2.nii.gz
        |    | series2_seg.nii.gz
        |    | ...

        The meta_data.json can be used to set values for study ids, series ids, patient names and additional dicom tags. The expected structure is as follows:

        {
            'Patients': 'all_same' | 'all_different' | [name1, name2, ..., nameN],
            'Study UIDs': 'all_same' | 'all_different' | [study1, study2, ..., studyN],
            'Study IDs': 'all_same' | 'all_different' | [study_uid1, study_uid2, ..., study_uidN], # TODO: probably just dont use them 
            'Modality': modality,   # see (0008,0060)
            'Series instance UID': [series_instance_uid1, series_instance_uid1, ..., series_instance_uidN]
            'Series descriptions': some_description | [desc1, desc2, ..., descN],
            
            'add_tags': {
                '/some/path/*nii.gz':{
                    '(xxxx|xxxx)': tag_value,
                    ...
                }
                
            }

            'seg_args': {
                'input_type': 'multi_label_seg' | 'single_label_segs',
                'single_label_seg_info': 'prostate',
                'multi_label_seg_info_json': 'seg_info.json'

            }

        }

        The field "add_tags" allows to set specific tags on all series matching the given file name pattern. At the moment this is just a simple glob pattern matching.
        If needed we could also add regex syntax here, but right for now this seems unnecessarily complex.

        The 'seg_args' parameter passes arguments to the Itk2DcmSegOperator which is responsible for the conversion of the segmentation objects if any are present.
        If there are no segmentation files 'seg_args' will be ignored.
        TODO: In theory it would be possible to derive a minimal set of segmentation args from the given files. Probably nice to have in the future.

        """
        datasets = next(os.walk(path))[1]

        for dataset in datasets:
            if dataset != "BMC":
                continue
            try:
                with open(os.path.join(f"/{path}", dataset,"meta_data.json"), "r") as meta_file:
                    meta_data = json.load(meta_file)
            except FileNotFoundError:
                meta_data = {}
            self.convert_dataset(Path(path) / dataset, meta_data)

    def convert_dataset(self, path, meta_data={}):

        cases = self.parser(path, log='Info')

        patients = meta_data.get("Patients") if meta_data.get("Patients") else "all_different"

        if patients == 'all_same':
            patients = ['single_patient' for _ in len(cases)]
        elif patients == 'all_different':
            patients = [f'patient_{i}' for i in range(len(cases))]
        else:
            if not isinstance(self.patients, list):
                raise AttributeError("Patients attribute must be 'all_same', 'all_different' or list of patients.") 
            for pat in self.patients:
                if not isinstance(pat, str):
                    raise AttributeError("Patient list must be list of strings.")

        # generate study uids
        study_instance_UIDs = meta_data.get("Study UIDs", 'all_same')
        if study_instance_UIDs == "all_same":
            study_instance_UIDs = [generate_uid(entropy_srcs=[str(patients[i])]) for i in range(len(patients))]
        elif study_instance_UIDs == "all_different":
            study_instance_UIDs = [generate_uid() for i in range(len(patients))]
        else:
            assert(isinstance(study_instance_UIDs, list))
            assert(len(study_instance_UIDs) == len(patients))


        # study_instance_UIDs = meta_data.get("Study UIDs") if meta_data.get("Study UIDs") else 
        # study_ids = meta_data.get("Study IDs") if meta_data.get("Study IDs") else str(path).split("/")[-1]
        
        series_descriptions = meta_data.get("Series Descriptions") if meta_data.get("Series descriptions") else [None for _ in range(len(cases))]
        modality = meta_data.get("Modality") if meta_data.get("Modality") else "OT"
        # seg_info = meta_data.get("seg_info")
        added_tags = meta_data.get("add_tags")
        
        seg_args = None
        seg_path = None
        # check if there are volumes with associated segmentations
        if any([s != None for _, s in cases]):
            # check if there are seg_args in meta_data
            try:
                seg_args = meta_data['seg_args']
                seg_path = path/seg_args['multi_label_seg_info_json'] if seg_args['multi_label_seg_info_json'] else None
            except KeyError:
                print("No arguments for Itk2DcmSegOperator found. Please provide 'seg_args' in the 'meta_data.json'.")
            
            # check if there is an seg_info file
            if not os.path.isfile(path/'seg_info.json'):
                raise FileNotFoundError("The study contains segmentation files, but no 'seg_info.json' file was found. Please add a 'seg_info.json' to each study directory.")
            else:
                pass


        

        for i, case in enumerate(cases):
            series_tag_values = {}
            # series_tag_values["0020|0010"] = # study_id
            series_tag_values["0020|000d"] = study_instance_UIDs[i]
            if added_tags is not None:
                for p in added_tags.keys():
                    p = f"/{p}" if p[0] != "/" else p
                    if str(case[0]) in glob.glob(f"{str(path)}{p}"):
                        series_tag_values= {**series_tag_values, **added_tags[p]}

            self.convert_series(
                Path(case[0]), 
                patient_id=patients[i], 
                series_description=series_descriptions[i], 
                modality=modality, 
                series_tag_values=series_tag_values,
                seg_args=seg_args,
                segmentation=case[1],
                seg_info_path=seg_path or None
            )
        

    def convert_series(self, case_path, patient_id, series_tag_values, seed='4242', segmentation=None, seg_args=None, seg_info_path=None, *args, **kwds):
        """
        :param data: data to process given as list of paths of the ".nii.gz" files to process.
        
        :returns: None type. Writes dicomS to $OPERATOR_OUT_DIR.
        """
        series_id = str(case_path).split('/')[-1].split('.')[0]
        series_description = kwds.get("series_description")
        dataset = str(case_path).split('/')[-2]
        if series_description == None:
            series_description = f"{str(case_path).split('/')[-2]}-{series_id}-{patient_id}"
    
        modality = kwds.get("modality") or "OT"
        if modality == "OT":
            warnings.warn("Modality is 'other' (OT). Unspecific modality does not not support correct representation of translation and rotation.", UserWarning)


        study_uid = series_tag_values['0020|000d']
        series_instance_UID = kwds.get("series_uid") or generate_uid(entropy_srcs=[patient_id, study_uid, series_id, seed])
        out_dir = make_out_dir(series_instance_UID, dataset=dataset, case=series_id, segmentation=segmentation, human_readable=False)

        new_img = sitk.ReadImage(case_path) 
        modification_time = time.strftime("%H%M%S")
        modification_date = time.strftime("%Y%m%d")

        direction = new_img.GetDirection()
        
        if "0008|0008" in series_tag_values.keys():
            pass
        else:
            series_tag_values["0008|0008"] = "DERIVED\\SECONDARY" # Image Type

        series_tag_values["0008|0031"] = modification_time # Series Time
        series_tag_values["0008|0021"] = modification_date # Series Date
        series_tag_values["0020|0037"] = '\\'.join(map(str, (direction[0], direction[3], direction[6], direction[1],direction[4],direction[7])))
        series_tag_values["0008|103e"] = series_description # Series Description
        series_tag_values["0020|000e"] = series_instance_UID
        series_tag_values["0008|0060"] = modality
        # series_tag_values["0020|0010"] = study_id
        series_tag_values["0010|0020"] = patient_id
        
        
        castFilter = sitk.CastImageFilter()
        castFilter.SetOutputPixelType(sitk.sitkInt16)
        imgFiltered = castFilter.Execute(new_img)
        
        for i in range(imgFiltered.GetDepth()):
            self.write_slices(imgFiltered, series_tag_values, i, out_dir/'dicoms')
        print("***", out_dir, "written.")
        
        

        if segmentation:
            print("### Checking for segmentation information.")
            shutil.copy2(segmentation, out_dir/'segmentations/')
            if seg_args is not None:
                print("### Extracting parameters for segmentation converter.")
                with open(out_dir/'segmentations'/"seg_args.json", "w") as f:
                    json.dump(seg_args, f)
            if seg_info_path:
                print("### Passing seg_info.json to segmentation converter.")
                #study_dir = '/'.join(str(path).split('/')[:-1])
                shutil.copy2(seg_info_path, out_dir/'segmentations/')
            print("### Processing segmentation parameters finished.")
            

    

    def write_slices(self, new_img, series_tag_values, i, out_dir):
        image_slice = new_img[:,:,i]
        writer = sitk.ImageFileWriter()
        writer.KeepOriginalImageUIDOn()
        
        patient_id = series_tag_values["0010|0020"]
        study_uid = series_tag_values["0020|000d"]
        series_uid = series_tag_values["0020|000e"]

        prefix = ".".join(series_uid.split(".")[:4])+"." # ugly syntax for strap the prefix from the series uid and reuse it for slice identifier but w/e
        slice_instance_uid = generate_uid(prefix=prefix, entropy_srcs=[patient_id, study_uid, series_uid, str(i)])

        series_tag_values["0008|0018"] = slice_instance_uid

        # set metadata shared by series
        for tag, value in series_tag_values.items():
            image_slice.SetMetaData(tag, value)

        # set slice specific metadata tags.
        image_slice.SetMetaData("0008|0012", time.strftime("%Y%m%d")) # Instance Creation Date
        image_slice.SetMetaData("0008|0013", time.strftime("%H%M%S")) # Instance Creation Time

        # image_slice.SetMetaData("0008|0060", "CT")

        # (0020, 0032) image position patient determines the 3D spacing between slices.
        image_slice.SetMetaData("0020|0032", '\\'.join(map(str,new_img.TransformIndexToPhysicalPoint((0,0,i))))) # Image Position (Patient)
        image_slice.SetMetaData("0020|0013", str(i)) # Instance Number

        # Write to the output directory and add the extension dcm, to force writing in DICOM format.
        writer.SetFileName(os.path.join(out_dir,'slice' + str(i).zfill(4) + '.dcm'))
        writer.Execute(image_slice)


    # def convert_segmentation(self, path, meta_json_path, *args, **kwds):
    #     meta = json.load(meta_json_path)
    #     template = pydicom_seg.template.from_dcmqi_metainfo('metainfo.json')
    #     nib.load(path)  


    # def validate_dicom(self, tags, valid_tags_csv):
    #     with open("/kaapanadevdata/dicom_tags_current.csv", 'r') as tagfile:
    #         reader = csv.reader(tagfile, delimiter='\t')
    #         valid_tags = {k: (v,d) for k,v,d,_ in reader }

    #     for tag, value in tags:
    #         if tag not in valid_tags.keys():
    #             raise AttributeError(f"Invalid dicom tag found in {meta_file}")


class Parser:
    """Parser for nifti or nrrd files. Lists all cases to process within a certain directory, along with the respective segmentation files. 
    Can be overwritten to support custom file trees.
    """
    def __init__(self) -> None:
        pass

    def __call__(self, path, *args, **kwds):
        
        # cases = [f for f in Path(path).rglob("Case*.nii.gz")]
        cases = [f for f in Path(path).rglob("*") if re.search(r"[cC]ase[0-9]+\.nii\.gz", str(f.name)) and not re.search(f"_{path}_[cC]ase\_out", str(f))]
        segs = [f for f in Path(path).rglob("*") if re.search(r"[cC]ase[0-9]+\_[sS]eg(mentation)?\.nii\.gz", str(f.name)) and not re.search(f"_{path}_/[cC]ase\_out", str(f))]
        if kwds.get("log") in ["Info", "Debug"]:
            print("----cases----")
            for x in cases: print(x)
            print("----segs-----")
            for x in segs: print(x)

        str_segs = [str(s) for s in segs]
        cases_with_segs = [c for c in cases if re.search(str(c).split(".")[0], "|".join(str_segs) )]
        cases_without_segs = [c for c in cases if c not in cases_with_segs]
        if len(cases_with_segs) > 0:

            print(f"Found {len(cases_without_segs)} cases without segmentations. Theses cases will be ignored. For more info run script with log='Debug' mode.")
            if kwds.get("log")=='Debug':
                print("----Cases without segmentations:----")
                for c in cases_without_segs:
                    print(c)
                print("----")
        
        # for c in cases_with_segs: print(c)
        cases_with_segs.sort()
        segs.sort()

        res = list(zip(cases_with_segs, segs))
        res.extend([(c, None) for c in cases_without_segs])

        return res


if __name__ == "__main__":
    # path = '/data/prostate_mri/'
    path = os.path.join("/" + os.environ.get("WORKFLOW_DIR"),os.environ.get("OPERATOR_IN_DIR"))
    converter = Nifti2DcmConverter()
    converter(path)