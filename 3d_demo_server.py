"""
3D Visualization MCP App Demo
Shows how to render 3D objects inside ChatGPT/Claude using Three.js
"""

from fastmcp import FastMCP

mcp = FastMCP("3D Visualizer")


@mcp.tool()
def view_3d_cube() -> str:
    """Display a rotating 3D cube."""

    html = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>3D Cube</title>
<style>
  body { margin: 0; overflow: hidden; background: #000; }
  canvas { width: 100%; height: 100vh; display: block; }
</style>
</head>
<body>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
// Scene setup
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);

// Create a cube
const geometry = new THREE.BoxGeometry(2, 2, 2);
const material = new THREE.MeshPhongMaterial({
  color: 0x00ff00,
  shininess: 100
});
const cube = new THREE.Mesh(geometry, material);
scene.add(cube);

// Add lights
const light = new THREE.PointLight(0xffffff, 1, 100);
light.position.set(5, 5, 5);
scene.add(light);

const ambientLight = new THREE.AmbientLight(0x404040);
scene.add(ambientLight);

camera.position.z = 5;

// Animation loop
function animate() {
  requestAnimationFrame(animate);
  cube.rotation.x += 0.01;
  cube.rotation.y += 0.01;
  renderer.render(scene, camera);
}

// Handle window resize
window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});

animate();
</script>
</body>
</html>"""

    return html


@mcp.tool()
def view_3d_molecule(formula: str = "H2O") -> str:
    """Display a 3D molecular structure."""

    # Simple sphere representation
    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Molecule: {formula}</title>
<style>
  body {{ margin: 0; overflow: hidden; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }}
  canvas {{ width: 100%; height: 100vh; display: block; }}
  .info {{
    position: absolute;
    top: 20px;
    left: 20px;
    color: white;
    font-family: Arial, sans-serif;
    font-size: 24px;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
  }}
</style>
</head>
<body>
<div class="info">Molecule: {formula}</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({{ antialias: true, alpha: true }});
renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);

// Water molecule (simplified)
// Oxygen (red sphere)
const oxygenGeo = new THREE.SphereGeometry(0.5, 32, 32);
const oxygenMat = new THREE.MeshPhongMaterial({{ color: 0xff0000 }});
const oxygen = new THREE.Mesh(oxygenGeo, oxygenMat);
scene.add(oxygen);

// Hydrogen atoms (white spheres)
const hydrogenGeo = new THREE.SphereGeometry(0.3, 32, 32);
const hydrogenMat = new THREE.MeshPhongMaterial({{ color: 0xffffff }});

const h1 = new THREE.Mesh(hydrogenGeo, hydrogenMat);
h1.position.set(-0.8, 0.6, 0);
scene.add(h1);

const h2 = new THREE.Mesh(hydrogenGeo, hydrogenMat);
h2.position.set(0.8, 0.6, 0);
scene.add(h2);

// Bonds (cylinders)
function createBond(start, end) {{
  const direction = new THREE.Vector3().subVectors(end, start);
  const length = direction.length();
  const bondGeo = new THREE.CylinderGeometry(0.05, 0.05, length, 8);
  const bondMat = new THREE.MeshPhongMaterial({{ color: 0xcccccc }});
  const bond = new THREE.Mesh(bondGeo, bondMat);

  bond.position.copy(start).add(direction.multiplyScalar(0.5));
  bond.quaternion.setFromUnitVectors(
    new THREE.Vector3(0, 1, 0),
    direction.normalize()
  );

  return bond;
}}

scene.add(createBond(oxygen.position, h1.position));
scene.add(createBond(oxygen.position, h2.position));

// Lights
const light1 = new THREE.PointLight(0xffffff, 1, 100);
light1.position.set(5, 5, 5);
scene.add(light1);

const light2 = new THREE.PointLight(0xffffff, 0.5, 100);
light2.position.set(-5, -5, -5);
scene.add(light2);

const ambientLight = new THREE.AmbientLight(0x404040);
scene.add(ambientLight);

camera.position.z = 3;

// Mouse interaction
let mouseX = 0, mouseY = 0;
document.addEventListener('mousemove', (e) => {{
  mouseX = (e.clientX / window.innerWidth) * 2 - 1;
  mouseY = -(e.clientY / window.innerHeight) * 2 + 1;
}});

// Animation
function animate() {{
  requestAnimationFrame(animate);

  // Rotate based on mouse
  scene.rotation.y = mouseX * 0.5;
  scene.rotation.x = mouseY * 0.5;

  renderer.render(scene, camera);
}}

window.addEventListener('resize', () => {{
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
}});

animate();
</script>
</body>
</html>"""

    return html


@mcp.tool()
def view_3d_data(values: str = "10,25,15,30,20") -> str:
    """Visualize data as 3D bar chart."""

    data_list = [int(x.strip()) for x in values.split(',')]

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>3D Data Visualization</title>
<style>
  body {{ margin: 0; overflow: hidden; background: #1a1a2e; }}
  canvas {{ width: 100%; height: 100vh; display: block; }}
</style>
</head>
<body>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({{ antialias: true }});
renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);

const data = {data_list};
const maxValue = Math.max(...data);

// Create 3D bars
data.forEach((value, index) => {{
  const height = (value / maxValue) * 5;
  const geometry = new THREE.BoxGeometry(0.8, height, 0.8);
  const hue = index / data.length;
  const material = new THREE.MeshPhongMaterial({{
    color: new THREE.Color().setHSL(hue, 0.8, 0.5),
    shininess: 100
  }});
  const bar = new THREE.Mesh(geometry, material);

  bar.position.x = (index - data.length / 2) * 1.2;
  bar.position.y = height / 2;

  scene.add(bar);
}});

// Grid
const gridHelper = new THREE.GridHelper(10, 10, 0x444444, 0x222222);
scene.add(gridHelper);

// Lights
const light = new THREE.DirectionalLight(0xffffff, 1);
light.position.set(5, 10, 5);
scene.add(light);

const ambientLight = new THREE.AmbientLight(0x404040);
scene.add(ambientLight);

camera.position.set(5, 5, 8);
camera.lookAt(0, 2, 0);

// Auto-rotate
function animate() {{
  requestAnimationFrame(animate);
  scene.rotation.y += 0.005;
  renderer.render(scene, camera);
}}

window.addEventListener('resize', () => {{
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
}});

animate();
</script>
</body>
</html>"""

    return html


if __name__ == "__main__":
    mcp.run()
