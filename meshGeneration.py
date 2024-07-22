# IMPORT DEPENDENCIES
import os
import torch
import numpy as np
import cv2 as cv
import open3d as o3d

from matplotlib import pyplot as plt
# pip install timm (for MiDaS model)

# GLOBAL VARIABLES
cam_calibration_dir_path = ".\calibration_images_new"
stereo_images_dir_path = ".\sample_stereo_images"
processed_images_dir_path = ".\processed"

# Open3D Translate Function Multiplier
X = 2000.0      

# FUNCTION DEFINITIONS
def get_image_pairs(dir_path: str, left_substr="image2", right_substr="image1"):
    '''Retrieve one or more image pairs (in '.jpg' or '.png' format) from the target directory based on their substring keywords (ex. \"imageX\"), 
       and each image has a file name and image data.
    '''
    image_pairs = []

    for file in os.listdir(dir_path):
        if (left_substr in file) and (".jpg" or ".png" in file):
            img1 = [[file, cv.imread(os.path.join(dir_path, file))], None]
            image_pairs.append(img1)

    for img1 in image_pairs:
        image_name = img1[0][0]
        img2 = image_name.replace(left_substr, right_substr)
        for file in os.listdir(dir_path):
            if file == img2:
                img1[1] = [file, cv.imread(os.path.join(dir_path, file))]
    
    return image_pairs

def get_calib_images(dir_path, additional_path=""):
    '''Retrieve one or more calibration images (in '.jpg' or '.png' format) from the target directory, specifically its file name and image data.\n
       Optional Args: additional_path = add a more specific path to the main directory 'dir_path'
    '''
    images = []

    # Retrieve all files located inside specific directory
    file_path = os.path.join(dir_path, additional_path)
    print(f" >>> Searching directory: \"{file_path}\"")
    for file_name in os.listdir(file_path):
            # If file has a format of .jpg or .png and is not null, append to images[]
            if (".jpg" or ".png") in file_name:
                img = cv.imread(os.path.join(file_path, file_name))
                if img is not None:
                    images.append(img)
    
    print(f" >>> Found {len(images)} images for calibration...")
    return images

def calibrate_stereo_cam(cam_calibration_dir_path, chessboard_size=(10,7), frame_size=(640, 480)):
    '''Generate stereo camera calibration parameters from a set of calibration images for each camera\n
       Optional Args: chessboard_size = specify the number of corners between the first and second row, and between the first and 
                                                             second columns, respectively
                               frame_size = specify the width and height of the calibration images (must be uniform for all calibration images)
    
    '''
    # Declare constants & initialize variables
    SIZE_OF_CHESSBOARD_SQUARES_MM = 20  # Size of each Chessboard Square (mm)
    images_left = []                    # Images to be used for Calibration (left CCamera)
    images_right = []                   # Images to be used for Calibration (Right Camera)
    obj_points = []                     # 3D Point in Real World Space
    img_points_left = []                # 2D Points in Image Plane (Left Camera)
    img_points_right = []               # 2D Points in Image Plane (Right Camera)
    
    # Define Termination Criteria; If number of iterations=30 reached or error is less than epsilon=0.001, calibration is terminated
    criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)

    # Prepare Object Points
    objp = np.zeros((chessboard_size[0] * chessboard_size[1], 3), np.float32)
    objp[:, :2] = np.mgrid[0:chessboard_size[0], 0:chessboard_size[1]].T.reshape(-1, 2)
    objp = objp * SIZE_OF_CHESSBOARD_SQUARES_MM

    # Retrieve Images for Calibration
    images_left = get_calib_images(cam_calibration_dir_path, "left_cam")     # Retrieve Images For Left Camera
    images_right = get_calib_images(cam_calibration_dir_path, "right_cam")   # Retrieve Images For Right Camera

    # Find the Chessboard Corners for Left Camera & Right Camera Images
    # print(" >>> Detecting Chessboard Corners...")

    img_count = 0
    for img_left, img_right in zip(images_left, images_right):
        # For each image pair, convert to grayscale for better results
        imgL = img_left
        imgR = img_right
        grayL = cv.cvtColor(imgL, cv.COLOR_BGR2GRAY)
        grayR = cv.cvtColor(imgR, cv.COLOR_BGR2GRAY)

        # Find the Chessboard Corners; If found, append object points and image points to respective lists
        retL, cornersL = cv.findChessboardCorners(grayL, chessboard_size, None)
        retR, cornersR = cv.findChessboardCorners(grayR, chessboard_size, None)

        if retL and retR == True:
            obj_points.append(objp)

            cornersL = cv.cornerSubPix(grayL, cornersL, (11,11), (-1,-1), criteria)
            img_points_left.append(cornersL)

            cornersR = cv.cornerSubPix(grayR, cornersR, (11,11), (-1,-1), criteria)
            img_points_right.append(cornersR)

            # Optional: Draw and Display the Corners
            # cv.drawChessboardCorners(imgL, chessboard_size, cornersL, retL)
            # cv.imshow("Left Camera: Image " + str(img_count + 1), imgL)
            # cv.drawChessboardCorners(imgR, chessboard_size, cornersR, retR)
            # cv.imshow("Right Camera: Image " + str(img_count + 1), imgR)
            # cv.waitKey(0)   # Press any key or close window directly
        
        else:
             print(f"   * ERROR: Unable to find corners for Image {img_count + 1}")
        img_count += 1

    cv.destroyAllWindows()

    # Calibrate the Left and Right Cameras
    retL, cameraMatrixL, distL, rvecsL, tvecsL = cv.calibrateCamera(obj_points, img_points_left, frame_size, None, None)
    heightL, widthL, channelsL = imgL.shape
    newCameraMatrixL, roi_L = cv.getOptimalNewCameraMatrix(cameraMatrixL, distL, (widthL, heightL), 1, (widthL, heightL))

    retR, cameraMatrixR, distR, rvecsR, tvecsR = cv.calibrateCamera(obj_points, img_points_right, frame_size, None, None)
    heightR, widthR, channelsR = imgR.shape
    newCameraMatrixR, roi_R = cv.getOptimalNewCameraMatrix(cameraMatrixR, distR, (widthR, heightR), 1, (widthR, heightR))

    # Fix Intrinsic Camera Matrices, so that only Rot, Trns, Emat and Fmat are calculated
    flags = 0
    flags |= cv.CALIB_FIX_INTRINSIC

    criteria_stereo = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001) # Same as termination criteria above
    retStereo, newCameraMatrixL, distL, newCameraMatrixR, distR, rot, trans, essentialMatrix, fundamentalMatrix = cv.stereoCalibrate(obj_points, img_points_left, img_points_right, newCameraMatrixL, distL, newCameraMatrixR, distR, grayL.shape[::-1], criteria_stereo, flags)

    # Optional: Calculate Reprojection Error
    mean_error = 0
    for i in range(len(obj_points)):
        imgpoints2, _ = cv.projectPoints(obj_points[i], rvecsR[i], tvecsR[i], newCameraMatrixR, distR)
        error = cv.norm(img_points_right[i], imgpoints2, cv.NORM_L2)/len(imgpoints2)
        mean_error += error

    # DEBUG: Display Total Error
    print(f" >>> Total Error: {mean_error/len(obj_points)}")

    # Rectify Stereo Camera Maps
    rectify_scale = 1
    rectL, rectR, projMatrixL, projMatrixR, Q, roi_L, roi_R= cv.stereoRectify(newCameraMatrixL, distL, newCameraMatrixR, distR, grayL.shape[::-1], rot, trans, rectify_scale,(0,0))

    stereoMapL = cv.initUndistortRectifyMap(newCameraMatrixL, distL, rectL, projMatrixL, grayL.shape[::-1], cv.CV_16SC2)
    stereoMapR = cv.initUndistortRectifyMap(newCameraMatrixR, distR, rectR, projMatrixR, grayR.shape[::-1], cv.CV_16SC2)

    # Save Calibration Parameters in a single .xml
    cv_file = cv.FileStorage('stereoMap.xml', cv.FILE_STORAGE_WRITE)

    cv_file.write('stereoMapL_x',stereoMapL[0])
    cv_file.write('stereoMapL_y',stereoMapL[1])
    cv_file.write('stereoMapR_x',stereoMapR[0])
    cv_file.write('stereoMapR_y',stereoMapR[1])
    cv_file.write('q', Q)

    cv_file.release()

def create_pcd(vertices, colors, filename):
	colors = colors.reshape(-1,3)
	vertices = np.hstack([vertices.reshape(-1,3),colors])

	ply_header = '''ply
		format ascii 1.0
		element vertex %(vert_num)d
		property float x
		property float y
		property float z
		property uchar red
		property uchar green
		property uchar blue
		end_header
		'''
	with open(filename, 'w') as f:
		f.write(ply_header %dict(vert_num=len(vertices)))
		np.savetxt(f,vertices,'%f %f %f %d %d %d')

# ================================= PROGRAM START ================================== #

# ----- 1. RETRIEVE STEREO IMAGES FROM TARGET DIRECTORY INTO IMAGE PAIR DATA STRUCTURE ----- #

# DEBUG: Display process & target directory
print(f"\nRETRIEVING STEREO IMAGES FROM: \"{stereo_images_dir_path}\"")     

image_pairs_raw = get_image_pairs(stereo_images_dir_path)

# DEBUG: Display number of image pairs found
print(f" >>> Found {len(image_pairs_raw)} image pairs...")                  

# DEBUG: Display each image filename & image data
# for image_pair in image_pairs_raw:                                          
#     cv.imshow(image_pair[1][0], image_pair[1][1])
#     cv.waitKey(0)
#     cv.imshow(image_pair[0][0], image_pair[0][1])
#     cv.waitKey(0)


#  ----- 2. PERFORM CAMERA CALIBRATION TO GENERATE CAMERA PARAMETERS ----------------------- #

# DEBUG: Display process & target directory
print(f"\nRETRIEVING CALIBRATION IMAGES FROM: \"{cam_calibration_dir_path}\"")     

calibrate_stereo_cam(cam_calibration_dir_path)

# DEBUG: Display target file for retrieving camera parameters
print(f"CAMERA PARAMETERS GENERATED WITH FILENAME: \"stereoMap.xml\"")             


# ----- 3. UNDISTORT STEREO IMAGES USING GENERATED CAMERA PARAMETERS ----------------------- #

# DEBUG: Display process & number of image pairs
print(f"\nUNDISTORTING {len(image_pairs_raw)} IMAGE PAIRS:")     

cam_params = cv.FileStorage("stereoMap.xml", cv.FILE_STORAGE_READ)

# DEBUG: Confirm whether camera parameters exist
if cam_params.isOpened():                                                               
    print(" >>> Using Camera Parameters with filename: \"stereoMap.xml\"")
else:
    print(" >>> No Camera Parameters found! Perform Camera Calibration first.")
    exit()

# Get parameters from each node
stereoMapL_x = cam_params.getNode("stereoMapL_x").mat()
stereoMapL_y = cam_params.getNode("stereoMapL_y").mat()
stereoMapR_x = cam_params.getNode("stereoMapR_x").mat()
stereoMapR_y = cam_params.getNode("stereoMapR_y").mat()

matrixQ = cam_params.getNode("q").mat()

image_pairs_undistorted = []
# Remap raw stereo images based on camera parameters
for imp in image_pairs_raw:
    undistortedL = cv.remap(imp[1][1], stereoMapL_x, stereoMapL_y, cv.INTER_LANCZOS4, cv.BORDER_CONSTANT, 0)
    undistortedR = cv.remap(imp[0][1], stereoMapR_x, stereoMapR_y, cv.INTER_LANCZOS4, cv.BORDER_CONSTANT, 0)

    # Save undistorted image pairs to new variable
    imp_undistorted = [[imp[0][0], undistortedR], [imp[1][0], undistortedL]]
    image_pairs_undistorted.append(imp_undistorted)

# DEBUG: Display number of undistorted image pairs
print(f"PERFORMED UNDISTORTION ON {len(image_pairs_undistorted)} IMAGE PAIRS")  

# DEBUG: Display each undistorted image filename & image data
# for image_pair in image_pairs_undistorted:                                             
#     cv.imshow(image_pair[1][0], image_pair[1][1])
#     cv.waitKey(0)
#     cv.imshow(image_pair[0][0], image_pair[0][1])
#     cv.waitKey(0)


# ----- 4. PERFORM IMAGE SEGMENTATION TO GENERATE OBJECT MASK ------------------------------ #

# DEBUG: Display process & number of image pairs
print(f"\nCREATING OBJECT MASKS FOR {len(image_pairs_undistorted)} IMAGE PAIRS:")     

image_masks = []

for im in image_pairs_undistorted:
    # Optional: Switch between im[0][1] and im[1][1] accordingly (which image will the mask be based on)
    img_raw = im[0][1]   

    # DEBUG: Show raw image (no segmentation performed)
    # cv.imshow("RAW", img_raw)
    # cv.waitKey(0)

    # Optional: Resize/Crop Image especially if large resolution, reduces processing time
    # img_raw = img_raw[0:640, 0:480]
    # img_raw = cv.resize(img_raw, None, fx=1.0, fx=1.0)

    # Convert Images to Grayscale, and perform thresholding for each image
    img_gray = cv.cvtColor(img_raw, cv.COLOR_BGR2GRAY)

    # Optional: Adjust Minimum and Maximum Threshold based on Contour results
    min_thres = 105     
    max_thres = 200

    # Generate Threshold for finding image Contours     
    _, th2 = cv.threshold(img_gray, min_thres, max_thres, cv.THRESH_BINARY)

    # Find Image Contours
    contours, hierarchy = cv.findContours(th2, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE)

    new_contours = []
    
    # Optional: Adjust Contour Size based on results
    contour_size = 700

    # Retrieve only Contours with a target minimum number of points (Contour Size)
    for i in range(len(contours)):
        if len(contours[i]) > contour_size:
            new_contours.append(contours[i])

    # DEBUG: Display remaining contours
    # cv.drawContours(img_raw, new_contours, -1, (0, 255, 0), thickness=2)
    # cv.imshow(im[1][0] + "Contour Result", img_raw)
    # cv.waitKey(0)

    # Create Mask from each image
    img_mask = np.zeros((img_raw.shape[0], img_raw.shape[1]), dtype="uint8")
    obj_mask = cv.drawContours(img_mask, new_contours, -1, 255, cv.FILLED)
    image_masks.append(obj_mask)

    # DEBUG: Display Mask Process Result
    # cv.imshow(im[1][0] + "Mask Result", obj_mask)
    # cv.waitKey(0)

# DEBUG: Display process & number of image masks
print(f" >>> Created {len(image_masks)} Object Masks...")     


# ----- 5. GENERATE DEPTH MAPS FROM STEREO IMAGES & APPLY OBJECT MASK ---------------------- #

# DEBUG: Display process & number of image pairs
print(f"\nCREATING DEPTH MAPS & POINT CLOUDS FOR {len(image_pairs_undistorted)} IMAGE PAIRS:")     

# Select which MiDaS model to download (MiDas_small < DPT_Hybrid < DPT_Large)
# midas = torch.hub.load("intel-isl/MiDaS", "MiDaS_small")
midas = torch.hub.load("intel-isl/MiDaS", "DPT_Hybrid")     # Best Results for Alcohol Bottle Test Object
# midas = torch.hub.load("intel-isl/MiDaS", "DPT_Large")

device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
midas.to(device)
midas.eval()

# Input Transformations
transforms = torch.hub.load("intel-isl/MiDaS", "transforms")
transform = transforms.small_transform

output_points = None
output_colors = None

for im, mask in zip(image_pairs_undistorted, image_masks):
    
    # Convert image to RGB format
    img_color = cv.cvtColor(im[0][1], cv.COLOR_BGR2RGB)
    img_batch = transform(img_color).to("cpu")

    # Generate Depth Map
    with torch.no_grad():
        prediction = midas(img_batch)

        prediction = torch.nn.functional.interpolate(
            prediction.unsqueeze(1),
            size=img_color.shape[:2],
            mode="bicubic",
            align_corners=False,
        ).squeeze()

    depth_map = prediction.cpu().numpy()
    img_depth = cv.normalize(depth_map, None, 0, 1, norm_type=cv.NORM_MINMAX, dtype=cv.CV_32F)
    
    # DEBUG: Display MiDaS Depth Map Results
    # cv.imshow("midas prediction", img_depth)
    # cv.waitKey(0)


# ----- 6. GENERATE POINT CLOUDS FROM THE DEPTH MAPS --------------------------------------- #

    # Reproject image to 3D using Camera Parameters (Q Matrix)
    points_3D = cv.reprojectImageTo3D(img_depth, matrixQ, handleMissingValues=False)

    # Apply Mask to image before generating the Point Cloud
    mask_map = mask > 0.4
    output_points = points_3D[mask_map]
    output_colors = img_color[mask_map]

    # Convert Depth Map to 8-bit Unsigned Integer Datatype & Add Color Data
    img_depth = (img_depth*255).astype(np.uint8)
    img_depth = cv.applyColorMap(img_depth , cv.COLORMAP_MAGMA)

    # Save Point Cloud with specified filename
    output_file = im[0][0].replace(im[0][0][17:], ".ply")

    # DEBUG: Display Color Map, Depth Map, and Object Mask
    fig = plt.figure(figsize=(10, 7))
    fig.suptitle(output_file)

    fig.add_subplot(1, 3, 1)
    plt.imshow(im[0][1])
    plt.axis("off")
    plt.title("Color")

    fig.add_subplot(1, 3, 2)
    plt.imshow(img_depth)
    plt.axis("off")
    plt.title("Depth")

    fig.add_subplot(1, 3, 3)
    plt.imshow(mask)
    plt.axis("off")
    plt.title("Mask")
    plt.show()
    
    # Generate Point Cloud 
    create_pcd(output_points, output_colors, output_file)

    # DEBUG: Display newly generated Point Clouds
    # pcd = o3d.io.read_point_cloud(output_file)
    # o3d.visualization.draw_geometries([pcd])

# DEBUG: Display number of depth maps & point clouds generated
print(f" >>> Created {len(image_pairs_undistorted)} Depth Maps and {len(image_pairs_undistorted)} Point Clouds...")   

# ----- 7a. REARRANGE POINT CLOUDS TO FORM 3D OBJECT --------------------------------------- #

# Import Point Clouds
pcd_front = o3d.io.read_point_cloud("20240521_image2_5.ply")
pcd_left  = o3d.io.read_point_cloud("20240521_image2_6.ply")
pcd_back  = o3d.io.read_point_cloud("20240521_image2_7.ply")
pcd_right = o3d.io.read_point_cloud("20240521_image2_8.ply")

# ------------------- FRONT -------------------- #
# Remove Outlier Points
cl, ind = pcd_front.remove_statistical_outlier(nb_neighbors=300, std_ratio=0.5)
pcd_front = pcd_front.select_by_index(ind)
cl, ind = pcd_front.remove_radius_outlier(nb_points=10, radius=300)
pcd_front = pcd_front.select_by_index(ind)

# Transform Point Cloud (Translate, Rotate, Scale)
pcd_front.translate((0, 0, 0))
pcd_front.rotate(
    pcd_front.get_rotation_matrix_from_xyz((
        0     - (np.pi * 16/128),    # X Rotation   
        np.pi + (np.pi *  3/128),    # Y Rotation   
        np.pi + (np.pi *  2/128)     # Z Rotation   
    )),
    center=pcd_front.get_center()
)
pcd_front.scale(1.0, center=pcd_front.get_center())

# DEBUG: Get Bounding Box
# box = pcd_front.get_axis_aligned_bounding_box()
# box.color = (1, 0, 0)

# DEBUG: Display Results
# o3d.visualization.draw_geometries([pcd_front, box])

# ------------------- BACK -------------------- #
# Remove Outlier Points
cl, ind = pcd_back.remove_statistical_outlier(nb_neighbors=300, std_ratio=0.5)
pcd_back = pcd_back.select_by_index(ind)
cl, ind = pcd_back.remove_radius_outlier(nb_points=10, radius=300)
pcd_back = pcd_back.select_by_index(ind)

# Transform Point Cloud (Translate, Rotate, Scale)
pcd_back.translate((-0.4 * X, -0.5 * X, -5.2 * X))
pcd_back.rotate(
    pcd_back.get_rotation_matrix_from_xyz((
        0     + (np.pi * 1/128),    # X Rotation
        0     + (np.pi * 3/128),    # Y Rotation
        np.pi + (np.pi * 3/128)     # Z Rotation
    )),
    center=pcd_back.get_center()
)
pcd_back.scale(1.0, center=pcd_back.get_center())

# Warp Point Cloud (to reduce curving)
pcd_back.transform([[1, 0, 0, 0], 
                    [0, 1, 0, 0], 
                    [0, -0.05, 1, 0], 
                    [0, 0, 0, 1]])

# DEBUG: Display Results
# o3d.visualization.draw_geometries([pcd_back, box])

# ------------------- LEFT -------------------- #
# Remove Outlier Points
cl, ind = pcd_left.remove_statistical_outlier(nb_neighbors=300, std_ratio=0.25)
pcd_left = pcd_left.select_by_index(ind)
cl, ind = pcd_left.remove_radius_outlier(nb_points=10, radius=250)
pcd_left = pcd_left.select_by_index(ind)

# Transform Point Cloud (Translate, Rotate, Scale)
pcd_left.translate((1.5 * X, -0.5 * X, -6 * X))
pcd_left.rotate(
    pcd_left.get_rotation_matrix_from_xyz((
        0     - (np.pi * 106/128),    # X Rotation
        np.pi + (np.pi *  56/128),    # Y Rotation
        np.pi - (np.pi * 102/128)     # Z Rotation
    )),
    center=pcd_left.get_center()
)
pcd_left.scale(0.9, center=pcd_left.get_center())

# DEBUG: Display Results
# o3d.visualization.draw_geometries([pcd_left, box])

# ------------------- RIGHT -------------------- #
# Remove Outlier Points
cl, ind = pcd_right.remove_statistical_outlier(nb_neighbors=300, std_ratio=0.25)
pcd_right = pcd_right.select_by_index(ind)
cl, ind = pcd_right.remove_radius_outlier(nb_points=7, radius=240)
pcd_right = pcd_right.select_by_index(ind)

# Transform Point Cloud (Translate, Rotate, Scale)
pcd_right.translate((-3.3 * X, -1 * X, -14 * X))
pcd_right.rotate(
    pcd_right.get_rotation_matrix_from_xyz((
        0     - (np.pi *  6/128),    # X Rotation   
        np.pi - (np.pi * 54/128),    # Y Rotation   
        np.pi + (np.pi *  4/128)     # Z Rotation   
    )),
    center=pcd_right.get_center()
)
pcd_right.scale(0.68, center=pcd_right.get_center())

# Warp Point Cloud (to reduce curving)
pcd_right.transform([[1, 0.1, 0, 0], 
                     [0, 1, 0, 0], 
                     [0, 0.1, 1, 0], 
                     [0, 0, 0, 1]])

# DEBUG: Display Results
# o3d.visualization.draw_geometries([pcd_right, box])


# ----- 7b. MERGE POINT CLOUDS INTO A SINGLE POINT CLOUD ----------------------------------- #



# DEBUG: Display process & number of image pairs
print(f"\nMERGING 4 POINT CLOUDS: ") 

# Merge all point clouds
merged_pcd = pcd_front + pcd_left + pcd_back + pcd_right

# DEBUG: Display Merged Point Cloud
# o3d.visualization.draw_geometries([merged_pcd])

# Remove Remaining Outlier Points
cl, ind = merged_pcd.remove_statistical_outlier(nb_neighbors=100, std_ratio=1.75)
merged_pcd = merged_pcd.select_by_index(ind)
cl, ind = merged_pcd.remove_radius_outlier(nb_points=10, radius=300)
merged_pcd = merged_pcd.select_by_index(ind)

# DEBUG: Display Cleaned Point Cloud
# o3d.visualization.draw_geometries([merged_pcd])

# Define merged Point Cloud filename
pcd_filename = "merged_pcd.ply"

# DEBUG: Display filename
print(f" >>> Saved Point Cloud with filename: \"{pcd_filename}\" ...")  

# Save Point Cloud to Directory
o3d.io.write_point_cloud(pcd_filename, merged_pcd)


# ----- 8. CONVERT POINT CLOUD INTO 3D MESH ------------------------------------------------ #

# DEBUG: Display process
print(f"\nGENERATING 3D MESH: ") 

# Perform Downsampling to reduce time in generating mesh
down_pcd = merged_pcd.voxel_down_sample(voxel_size=1000)

# DEBUG: Display downsampled Point Cloud
# o3d.visualization.draw_geometries([down_pcd])

# Estimate Point Cloud Normals to determine mesh face orientations
down_pcd.normals = o3d.utility.Vector3dVector(np.zeros((1, 3)))
down_pcd.estimate_normals()

# DEBUG: Display Point Cloud Normals
# o3d.visualization.draw_geometries([down_pcd], point_show_normal=True)

# ---------------------------------------------------------------- #
# MESH GENERATION METHOD 1: CREATE MESH FROM CONVEX HULL
# Result: Creates a fully-formed 3D Mesh, however the colors from the point clouds was not retained
hull_mesh, _ = down_pcd.compute_convex_hull()
hull_mesh.compute_vertex_normals()

# DEBUG: Display generated Mesh
o3d.visualization.draw_geometries([hull_mesh], mesh_show_back_face=True)

# DEBUG: Display method & filename
print(f" >>> Generated 3D Mesh using Convex Hull Method...")  
print(f" >>> Saved 3D Mesh with filename: \"mesh_hull.ply\" ...")  

# Save Mesh file to directory
o3d.io.write_triangle_mesh("mesh_hull.ply", hull_mesh)

# ---------------------------------------------------------------- #


# ---------------------------------------------------------------- #
# MESH GENERATION METHOD 2: CREATE MESH FROM BALL PIVOTING ALGORITHM
# Result: Creates a 3D Mesh with the colors retained, however there are holes in the geometry that must be filled
radii = 2.0 * np.mean(down_pcd.compute_nearest_neighbor_distance())
bp_mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_ball_pivoting(down_pcd, o3d.utility.DoubleVector([radii, radii * 10])) 

# DEBUG: Display generated Mesh
o3d.visualization.draw_geometries([bp_mesh], mesh_show_back_face=True)

# DEBUG: Display method & filename
print(f" >>> Generated 3D Mesh using Ball Pivoting Algorithm...") 
print(f" >>> Saved 3D Mesh with filename: \"mesh_bp.ply\" ...") 

# Save Mesh file to directory
o3d.io.write_triangle_mesh("mesh_bp.ply", bp_mesh)
# ---------------------------------------------------------------- #

print(f"3D MESH SUCCESSFULLY GENERATED FROM STEREO IMAGES!\n") 

# ================================== PROGRAM END =================================== #