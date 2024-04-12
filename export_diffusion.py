bl_info = {
    "name": "Export Camera Animation to Deforum collab/webui",
    "author": "Kewk",
    "version": (1, 4, 0),
    "blender": (4, 1, 0),
    "location": "File > Export > Diffusion String",
    "description": "Export camera animations formatted for use in Deforum",
    "warning": "",
    "wiki_url": "",
    "category": "Import-Export",
}

import bpy
from bpy_extras.io_utils import ImportHelper, ExportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty, IntProperty, FloatProperty
from bpy.types import Operator

def roundZero(num, magnitude_thresh=0.00001):
    if abs(num) > magnitude_thresh:
        return num
    else:
        return 0

def arr_to_keyframes(arr):
    keyframes = ""
    for i, val in enumerate(arr):
        val = roundZero(val)
        last_is_same = i > 0 and isclose(val, roundZero(arr[i-1]))
        next_is_same = (i+1) < len(arr) and isclose(val, roundZero(arr[i+1]))
        omit = last_is_same and next_is_same
        if not omit:
            keyframes += f"{i}:({val}),"
    return keyframes

def cameras_to_string(context, startFrame, endFrame, cameras, translation_scale=50, output_camcode=True, output_json=False, output_raw_frames=False):
    scene = context.scene
    currentFrame = scene.frame_current
    if len(cameras) == 0:
        print("Nothing selected!")
        return "No Cameras selected for export"
    export_string = ""
    for sel in cameras:
        scene.frame_set(startFrame)
        translation_x = []
        translation_y = []
        translation_z = []
        rotation_3d_x = []
        rotation_3d_y = []
        rotation_3d_z = []
        oldMat = sel.matrix_world.copy()
        oldRot = oldMat.to_quaternion()
        for frame in range(startFrame+1, endFrame):
            scene.frame_set(frame)
            newMat = sel.matrix_world.copy()
            newRot = newMat.to_quaternion()
            worldToLocal = newMat.inverted()
            wlRot = worldToLocal.to_quaternion()
            posDiff = newMat.to_translation() - oldMat.to_translation()
            posDiffLocal = wlRot @ posDiff
            translation_x.append(translation_scale*posDiffLocal.x)
            translation_y.append(translation_scale*posDiffLocal.y)
            translation_z.append(-translation_scale*posDiffLocal.z)
            rotDiff = oldRot.rotation_difference(newRot).to_euler("XYZ")
            rotation_3d_x.append(degrees(rotDiff.x))
            rotation_3d_y.append(degrees(-rotDiff.y))
            rotation_3d_z.append(degrees(-rotDiff.z))
            oldMat = newMat
            oldRot = newRot
        if not output_raw_frames:
            export_string += f"\nCamera Export: {sel.name}\n"
            export_string += f'translation_x = "{arr_to_keyframes(translation_x)}" #@param {{type:"string"}}\n'
            export_string += f'translation_y = "{arr_to_keyframes(translation_y)}" #@param {{type:"string"}}\n'
            export_string += f'translation_z = "{arr_to_keyframes(translation_z)}" #@param {{type:"string"}}\n'
            export_string += f'rotation_3d_x = "{arr_to_keyframes(rotation_3d_x)}" #@param {{type:"string"}}\n'
            export_string += f'rotation_3d_y = "{arr_to_keyframes(rotation_3d_y)}" #@param {{type:"string"}}\n'
            export_string += f'rotation_3d_z = "{arr_to_keyframes(rotation_3d_z)}" #@param {{type:"string"}}\n'
        if output_camcode:
            export_string += f'cam_code:\n(translation_x,translation_y,translation_z,rotation_3d_x,rotation_3d_y,rotation_3d_z) = ("{arr_to_keyframes(translation_x)}", "{arr_to_keyframes(translation_y)}", "{arr_to_keyframes(translation_z)}", "{arr_to_keyframes(rotation_3d_x)}", "{arr_to_keyframes(rotation_3d_y)}", "{arr_to_keyframes(rotation_3d_z)}")\n'
        if output_json:
            jsondict = {
                "translation_x": translation_x,
                "translation_y": translation_y,
                "translation_z": translation_z,
                "rotation_3d_x": rotation_3d_x,
                "rotation_3d_y": rotation_3d_y,
                "rotation_3d_z": rotation_3d_z
            }
            export_string += f"JSON:\n {json.dumps(jsondict)}\n"
        if output_raw_frames:
            raw_frames = {
                "translation_x": translation_x,
                "translation_y": translation_y,
                "translation_z": translation_z,
                "rotation_3d_x": rotation_3d_x,
                "rotation_3d_y": rotation_3d_y,
                "rotation_3d_z": rotation_3d_z
            }
            for key, arr in raw_frames.items():
                raw_frame_str = ""
                last_val = None
                for i, val in enumerate(arr):
                    if last_val is None or not isclose(val, last_val):
                        raw_frame_str += f"{i}:({val}),"
                    last_val = val
                raw_frame_str = raw_frame_str.rstrip(",")
                export_string += f"\nRaw frames for {key}:\n{raw_frame_str}\n"
        export_string += "\n"
    scene.frame_set(currentFrame)
    return export_string

def write_camera_data(context, filepath, start, end, cams, scale, output_camcode, output_json, output_raw_frames):
    print("running write_camera_data...")
    outputString = cameras_to_string(context, start, end, cams, scale, output_camcode, output_json, output_raw_frames)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"Export frames {start}
