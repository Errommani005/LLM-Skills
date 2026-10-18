// toon.gdshader - THE one shader every 3D model uses (style rule: no per-asset materials).
// WHAT:  reads color from the shared palette image and lights it in flat bands.
// USE:   make ONE ShaderMaterial with this shader, assign it to every mesh. Never make another shader.
shader_type spatial;
render_mode diffuse_toon, specular_disabled;

uniform sampler2D palette : source_color, filter_nearest;   // shared/palette.png: one swatch per color
uniform vec4 tint : source_color = vec4(1.0);               // optional per-object tint (keep white by default)

void fragment() {
	ALBEDO = texture(palette, UV).rgb * tint.rgb;
	ROUGHNESS = 1.0;
}
