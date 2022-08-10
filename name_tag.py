import harfang as hg
from math import pi

def draw_name_tag(vtx, vtx_4, robot_position, shader, shader_1, vid_scene_opaque, text, font, font_prg, text_uniform_values, text_render_state, cam_world):
	front = hg.GetZ(cam_world)
	right = hg.GetX(cam_world)
	up = hg.GetY(cam_world)

	text_rect = hg.ComputeTextRect(font, text)
	width_ratio = text_rect.ex / 250

	vtx.Clear()
	vtx.Begin(0).SetPos(robot_position).End()
	vtx.Begin(1).SetPos(hg.Vec3(robot_position.x, robot_position.y + 3, robot_position.z)).End()
	hg.DrawLines(vid_scene_opaque, vtx, shader)

	name_tag_position = hg.Vec3(robot_position.x, robot_position.y + 3.5, robot_position.z)

	hg.DrawText(vid_scene_opaque, font, text, font_prg, 'u_tex', 0, hg.TransformationMat4(name_tag_position, 
	# front
	hg.GetRotation(cam_world) + hg.Vec3(pi, 0, 0)
	 , hg.Vec3(0.005, 0.005, 0.005)), name_tag_position, hg.DTHA_Center, hg.DTVA_Center,
	 text_uniform_values, [], text_render_state, 1)

	vtx_4.Clear()
	vtx_4.Begin(0).SetPos(name_tag_position - (right * width_ratio) + (up * 0.4)).End()
	vtx_4.Begin(1).SetPos(name_tag_position + (right * width_ratio) + (up * 0.4)).End()
	vtx_4.Begin(2).SetPos(name_tag_position + (right * width_ratio) - (up * 0.6)).End()


	hg.DrawTriangles(vid_scene_opaque, vtx_4, shader_1, text_render_state, 2)
	vtx_4.Clear()
	vtx_4.Begin(0).SetPos(name_tag_position - (right * width_ratio) + (up * 0.4)).End()
	vtx_4.Begin(1).SetPos(name_tag_position + (right * width_ratio) - (up * 0.6)).End()
	vtx_4.Begin(2).SetPos(name_tag_position - (right * width_ratio) - (up * 0.6)).End()

	hg.DrawTriangles(vid_scene_opaque, vtx_4, shader_1, text_render_state, 2)

