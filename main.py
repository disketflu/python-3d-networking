import harfang as hg
import socket
import threading
import pickle
import time
from utils import RangeAdjust
from statistics import median_low, median_high
from name_tag import draw_name_tag

# Init socket and server-linked variables
UDP_IP = "127.0.0.1"
UDP_PORT = 5005

sock = socket.socket(socket.AF_INET,
					 socket.SOCK_DGRAM)

MESSAGE = [0, 0, 0, 0, 0, 0] # MESSAGE CODE, POS_X, POS_Z, ROT_X_Y_Z
players = []
old_players = players
players_spawned = 0
players_instances = []
time_deltas = []
time_awaiting_packet = 0

def handleSnd():
	global MESSAGE
	while True:
		data = pickle.dumps(MESSAGE)
		sock.sendto(data, (UDP_IP, UDP_PORT))
		time.sleep(0.1)

def handleRcv():
	global players, old_players
	while True:
		try:
			data, addr = sock.recvfrom(1024)
			decoded_data = pickle.loads(data)
			if decoded_data[0] == 1:
				old_players = players.copy()
				players = decoded_data[1]
				players.append(time.time())

		except Exception as err:
			print(err)

threading.Thread(target=handleSnd).start()
threading.Thread(target=handleRcv).start()

# Init Harfang
hg.InputInit()
hg.WindowSystemInit()

res_x, res_y = 1280, 720
win = hg.RenderInit('3D Server - Client Scene', res_x, res_y, hg.RF_VSync | hg.RF_MSAA4X)

pipeline = hg.CreateForwardPipeline()
res = hg.PipelineResources()

hg.AddAssetsFolder("server_client_demo_compiled")
hg.ImGuiInit(10, hg.LoadProgramFromAssets('core/shader/imgui'), hg.LoadProgramFromAssets('core/shader/imgui_image'))
line_shader = hg.LoadProgramFromAssets('core/shader/white')
name_shader = hg.LoadProgramFromAssets('core/shader/grey')
font = hg.LoadFontFromAssets('font/ticketing.ttf', 96)
font_prg = hg.LoadProgramFromAssets('core/shader/font')
text_uniform_values = [hg.MakeUniformSetValue('u_color', hg.Vec4(1, 1, 1))]
text_render_state = hg.ComputeRenderState(hg.BM_Alpha, hg.DT_Always, hg.FC_Disabled)

vtx_layout = hg.VertexLayout()
vtx_layout.Begin()
vtx_layout.Add(hg.A_Position, 3, hg.AT_Float)
vtx_layout.End()

# load scene
scene = hg.Scene()
hg.LoadSceneFromAssets("level_1_full.scn", scene, res, hg.GetForwardPipelineInfo())
cam = scene.GetNode('Camera')
cam_rot = scene.GetNode('camrotation')

# AAA pipeline
pipeline_aaa_config = hg.ForwardPipelineAAAConfig()
pipeline_aaa = hg.CreateForwardPipelineAAAFromAssets("core", pipeline_aaa_config, hg.BR_Equal, hg.BR_Equal)
pipeline_aaa_config.sample_count = 1
pipeline_aaa_config.motion_blur = 0


# input devices and fps controller states
keyboard = hg.Keyboard()
mouse = hg.Mouse()

# main loop
frame = 0
show_lerp = True
show_pred = True
show_real = True
vid_scene_opaque = 0
vtx_2 = hg.Vertices(vtx_layout, 2)
vtx_4 = hg.Vertices(vtx_layout, 4)


while not hg.ReadKeyboard().Key(hg.K_Escape) and hg.IsWindowOpen(win):
	keyboard.Update()
	mouse.Update()
	dt = hg.TickClock()

	if len(players) - 1 > players_spawned:
		player_node, _  = hg.CreateInstanceFromAssets(scene, hg.TransformationMat4(hg.Vec3(players[players_spawned][0], 0, players[players_spawned][1]), hg.Vec3(players[players_spawned][2], players[players_spawned][3], players[players_spawned][4])), "objects_library/players/yellow_robot.scn", res, hg.GetForwardPipelineInfo())
		player_lerp_node, _  = hg.CreateInstanceFromAssets(scene, hg.TransformationMat4(hg.Vec3(players[players_spawned][0], 0, players[players_spawned][1]), hg.Vec3(players[players_spawned][2], players[players_spawned][3], players[players_spawned][4])), "objects_library/players/ghost_uninterpolated_robot.scn", res, hg.GetForwardPipelineInfo())
		player_pred_node, _  = hg.CreateInstanceFromAssets(scene, hg.TransformationMat4(hg.Vec3(players[players_spawned][0], 0, players[players_spawned][1]), hg.Vec3(players[players_spawned][2], players[players_spawned][3], players[players_spawned][4])), "objects_library/players/ghost_predict_robot.scn", res, hg.GetForwardPipelineInfo())

		players_instances.append([[player_node, player_lerp_node, player_pred_node], players_spawned])
		players_spawned += 1
		print("Spawned a new player")

	for pinstance in players_instances:
		if len(old_players) == len(players):
			player_transform = pinstance[0][0].GetTransform()
			player_nolerp_transform = pinstance[0][1].GetTransform()
			player_pred_transform = pinstance[0][2].GetTransform()
			player_id = pinstance[1]
			player_updated_pos = hg.Vec3(players[player_id][0], 0, players[player_id][1])
			player_updated_rot = hg.Vec3(players[player_id][2], players[player_id][3], players[player_id][4])
			player_old_pos = hg.Vec3(old_players[player_id][0], 0, old_players[player_id][1])
			player_old_rot = hg.Vec3(old_players[player_id][2], old_players[player_id][3], old_players[player_id][4])
			updated_time = players[-1]
			old_time = old_players[-1]
			time_diff = updated_time - old_time

			time_deltas.append(time_diff)
			time_deltas.sort()
			if len(time_deltas) > 20: #linearize the delta for the last 20 packets only 
				time_deltas.pop()

			avg_time_diff = (median_low(time_deltas) + median_high(time_deltas)) / 2

			time_end = updated_time + avg_time_diff
			if time.time() < time_end:
				adjusted_time = RangeAdjust(time.time(), updated_time, time_end, 0, 1)
				wanted_pos = hg.Lerp(player_old_pos, player_updated_pos, adjusted_time)
				wanted_rot = hg.Lerp(player_old_rot, player_updated_rot, adjusted_time)
				draw_name_tag(vtx_2, vtx_4, wanted_pos, line_shader, name_shader, vid_scene_opaque, "Remote " + str(pinstance[1] + 1), font, font_prg, text_uniform_values, text_render_state, cam.GetTransform().GetWorld())
				if show_lerp:
					player_transform.SetPos(wanted_pos)
					player_transform.SetRot(wanted_rot)
				else:
					player_transform.SetPos(hg.Vec3(-100, -100, -100))

				# prediction
				pos_dif = player_updated_pos - player_old_pos
				predicted_pos = player_updated_pos + (pos_dif * adjusted_time)
				rot_dif = player_updated_rot - player_old_rot
				predicted_rot = player_updated_rot + (rot_dif * adjusted_time)
				if show_pred:
					player_pred_transform.SetPos(predicted_pos)
					player_pred_transform.SetRot(predicted_rot)
				else:
					player_pred_transform.SetPos(hg.Vec3(-100, -100, -100))

				time_awaiting_packet = 0
			else:
				time_awaiting_packet += dt
				draw_name_tag(vtx_2, vtx_4, player_updated_pos, line_shader, name_shader, vid_scene_opaque, "Remote " + str(pinstance[1] + 1), font, font_prg, text_uniform_values, text_render_state, cam.GetTransform().GetWorld())

			if show_real:
				player_nolerp_transform.SetPos(hg.Vec3(players[player_id][0], 0, players[player_id][1]))
				player_nolerp_transform.SetRot(hg.Vec3(players[player_id][2], players[player_id][3], players[player_id][4]))			
			else:
				player_nolerp_transform.SetPos(hg.Vec3(-100, -100, -100))

	trs = scene.GetNode('red_player').GetTransform()
	pos = trs.GetPos()
	rot = trs.GetRot()

	MESSAGE = [0, pos.x, pos.z, rot.x, rot.y, rot.z]
	world = hg.RotationMat3(rot.x, rot.y, rot.z)
	front = hg.GetZ(world)

	min_node_pos = scene.GetNode('area_min').GetTransform().GetPos()
	max_node_pos = scene.GetNode('area_max').GetTransform().GetPos()
	min_x = min_node_pos.x
	min_z = min_node_pos.z
	max_x = max_node_pos.x
	max_z = max_node_pos.z

	simulated_pos_forward = pos + front * (hg.time_to_sec_f(dt) * 10)
	simulated_pos_backward = pos - front * (hg.time_to_sec_f(dt) * 10)
	if True and simulated_pos_forward.x < max_x and simulated_pos_forward.x > min_x and simulated_pos_forward.z < max_z and simulated_pos_forward.z > min_z:
		trs.SetPos(pos + front * (hg.time_to_sec_f(dt) * 10))
	if keyboard.Down(hg.K_Down) and simulated_pos_backward.x < max_x and simulated_pos_backward.x > min_x and simulated_pos_backward.z < max_z and simulated_pos_backward.z > min_z:
		trs.SetPos(pos - front * (hg.time_to_sec_f(dt) * 10))
	if True:
		trs.SetRot(hg.Vec3(rot.x, rot.y + (hg.time_to_sec_f(dt)), rot.z))
	if keyboard.Down(hg.K_Left):
		trs.SetRot(hg.Vec3(rot.x, rot.y - (hg.time_to_sec_f(dt)), rot.z))

	scene.Update(dt)
	vid, pass_ids = hg.SubmitSceneToPipeline(0, scene, hg.IntRect(0, 0, res_x, res_y), True, pipeline, res, pipeline_aaa, pipeline_aaa_config, frame)

	vid_scene_opaque = hg.GetSceneForwardPipelinePassViewId(pass_ids, hg.SFPP_Opaque)

	draw_name_tag(vtx_2, vtx_4, pos, line_shader, name_shader, vid_scene_opaque, "Local", font, font_prg, text_uniform_values, text_render_state, cam.GetTransform().GetWorld())

	hg.ImGuiBeginFrame(res_x, res_y, dt, mouse.GetState(), keyboard.GetState())
	hg.SetView2D(0, 0, 0, res_x, res_y, -1, 0, hg.CF_Color | hg.CF_Depth, hg.Color.Green, 1, 0)

	hg.ImGuiSetNextWindowPos(hg.Vec2(10, 10))
	hg.ImGuiSetNextWindowSize(hg.Vec2(300, 150), hg.ImGuiCond_Once)

	if hg.ImGuiBegin('Online Robots Config'):
		hg.ImGuiTextColored(hg.Color.Red, "Time waiting for packet : " + str(hg.time_to_sec_f(time_awaiting_packet)))
		hg.ImGuiSeparator()
		was_changed_lerp, show_lerp = hg.ImGuiCheckbox('Show Linear Interpolation', show_lerp)
		was_changed_pred, show_pred = hg.ImGuiCheckbox('Show Prediction', show_pred)
		was_changed_real, show_real = hg.ImGuiCheckbox('Show Real Position', show_real)

	hg.ImGuiEnd()

	hg.ImGuiEndFrame(255)

	frame = hg.Frame()
	hg.UpdateWindow(win)

hg.RenderShutdown()
hg.DestroyWindow(win)