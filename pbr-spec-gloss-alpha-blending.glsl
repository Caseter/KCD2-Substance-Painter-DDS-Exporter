//- Allegorithmic Spec/Gloss and opacity PBR shader
//- Edit by Christopher Pawliuk to add Alpha Blending for Spec/Gloss
//- ================================================
//-
//- Import from libraries.
import lib-pbr.glsl
import lib-emissive.glsl
import lib-pom.glsl
import lib-utils.glsl

// Link Spec/Gloss MDL for Iray
//: metadata {
//:   "mdl":"mdl::alg::materials::physically_specular_glossiness::physically_specular_glossiness"
//: }

//- Show back faces as there may be holes in front faces.
//: state cull_face off

//- Enable alpha blending
//: state blend over

//- Channels needed for spec/gloss workflow are bound here.
//: param auto channel_diffuse
uniform SamplerSparse diffuse_tex;
//: param auto channel_specular
uniform SamplerSparse specularcolor_tex;
//: param auto channel_glossiness
uniform SamplerSparse glossiness_tex;
//: param auto channel_specularlevel
uniform SamplerSparse specularlevel_tex;
//: param auto channel_opacity
uniform SamplerSparse opacity_tex;

//- Shader entry point.
void shade(V2F inputs)
{
  // Apply parallax occlusion mapping if possible
  vec3 viewTS = worldSpaceToTangentSpace(getEyeVec(inputs.position), inputs);
  applyParallaxOffset(inputs, viewTS);

  float glossiness = getGlossiness(glossiness_tex, inputs.sparse_coord);
  vec3 specColor = getSpecularColor(specularcolor_tex, inputs.sparse_coord);
  vec3 diffColor = getDiffuse(diffuse_tex, inputs.sparse_coord) * (vec3(1.0) - specColor);
  // Get detail (ambient occlusion) and global (shadow) occlusion factors
  float occlusion = getAO(inputs.sparse_coord) * getShadowFactor();

  LocalVectors vectors = computeLocalFrame(inputs);

  // Feed parameters for a physically based BRDF integration
  alphaOutput(getOpacity(opacity_tex, inputs.sparse_coord));
  emissiveColorOutput(pbrComputeEmissive(emissive_tex, inputs.sparse_coord));
  albedoOutput(diffColor);
  diffuseShadingOutput(occlusion * envIrradiance(vectors.normal));
  specularShadingOutput(occlusion * pbrComputeSpecular(vectors, specColor, 1.0 - glossiness));
sssCoefficientsOutput(getSSSCoefficients(inputs.sparse_coord));
}