(function () {
  "use strict";

  const EMBER = 0xff6a1f;
  const STEEL = 0x5eead4;
  const VIOLET = 0xa78bfa;

  let container, renderer, scene, camera, animationId;
  let coreGroup, orbitGroup, sparkGeo, particles;
  let mouseX = 0, mouseY = 0;
  let visible = true;
  let reducedMotion = false;

  function makeGlowMaterial(color, opacity) {
    return new THREE.MeshBasicMaterial({
      color,
      transparent: true,
      opacity: opacity || 0.85,
      wireframe: true,
    });
  }

  function buildCore() {
    coreGroup = new THREE.Group();

    coreGroup.add(new THREE.Mesh(
      new THREE.OctahedronGeometry(1.1, 0),
      makeGlowMaterial(EMBER, 0.55)
    ));

    coreGroup.add(new THREE.Mesh(
      new THREE.IcosahedronGeometry(1.65, 1),
      makeGlowMaterial(STEEL, 0.28)
    ));

    coreGroup.add(new THREE.Mesh(
      new THREE.IcosahedronGeometry(2.35, 0),
      makeGlowMaterial(VIOLET, 0.14)
    ));

    const ringGeo = new THREE.TorusGeometry(2.8, 0.025, 8, 64);
    for (let i = 0; i < 3; i++) {
      const ring = new THREE.Mesh(ringGeo, new THREE.MeshBasicMaterial({
        color: STEEL,
        transparent: true,
        opacity: 0.35,
      }));
      ring.rotation.x = Math.PI / 2 + i * 0.55;
      ring.rotation.y = i * 0.4;
      coreGroup.add(ring);
    }

    scene.add(coreGroup);
  }

  function buildOrbitNodes() {
    orbitGroup = new THREE.Group();
    const nodes = [];
    const count = 8;
    const radius = 3.6;

    for (let i = 0; i < count; i++) {
      const angle = (i / count) * Math.PI * 2;
      const y = Math.sin(i * 1.3) * 1.2;
      const x = Math.cos(angle) * radius;
      const z = Math.sin(angle) * radius;

      const box = new THREE.Mesh(
        new THREE.BoxGeometry(0.38, 0.38, 0.38),
        new THREE.MeshBasicMaterial({
          color: i % 2 === 0 ? STEEL : EMBER,
          transparent: true,
          opacity: 0.75,
          wireframe: true,
        })
      );
      box.position.set(x, y, z);
      box.userData.baseAngle = angle;
      orbitGroup.add(box);
      nodes.push(box);
    }

    const lineMat = new THREE.LineBasicMaterial({ color: STEEL, transparent: true, opacity: 0.18 });

    nodes.forEach(function (node, i) {
      orbitGroup.add(new THREE.Line(
        new THREE.BufferGeometry().setFromPoints([
          new THREE.Vector3(0, 0, 0),
          node.position.clone(),
        ]),
        lineMat
      ));

      const next = nodes[(i + 1) % count];
      orbitGroup.add(new THREE.Line(
        new THREE.BufferGeometry().setFromPoints([
          node.position.clone(),
          next.position.clone(),
        ]),
        lineMat.clone()
      ));
    });

    scene.add(orbitGroup);
  }

  function buildSparks() {
    const count = reducedMotion ? 120 : 400;
    sparkGeo = new THREE.BufferGeometry();
    const positions = new Float32Array(count * 3);
    const velocities = [];

    for (let i = 0; i < count; i++) {
      positions[i * 3] = (Math.random() - 0.5) * 1.5;
      positions[i * 3 + 1] = (Math.random() - 0.5) * 1.5;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 1.5;
      velocities.push({
        x: (Math.random() - 0.5) * 0.012,
        y: Math.random() * 0.025 + 0.008,
        z: (Math.random() - 0.5) * 0.012,
        life: Math.random(),
      });
    }

    sparkGeo.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    sparkGeo.userData.velocities = velocities;

    particles = new THREE.Points(sparkGeo, new THREE.PointsMaterial({
      color: EMBER,
      size: 0.045,
      transparent: true,
      opacity: 0.75,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    }));

    scene.add(particles);
  }

  function onResize() {
    if (!renderer || !camera || !container) return;
    const w = container.clientWidth;
    const h = container.clientHeight;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h, false);
  }

  function onMouseMove(e) {
    mouseX = (e.clientX / window.innerWidth - 0.5) * 2;
    mouseY = (e.clientY / window.innerHeight - 0.5) * 2;
  }

  function animate() {
    animationId = requestAnimationFrame(animate);
    if (!visible || !coreGroup) return;

    const t = performance.now() * 0.001;

    coreGroup.rotation.y = t * 0.35;
    coreGroup.rotation.x = Math.sin(t * 0.4) * 0.15;

    if (orbitGroup) {
      orbitGroup.rotation.y = -t * 0.18;
      orbitGroup.children.forEach(function (child, i) {
        if (child.userData.baseAngle !== undefined) {
          child.rotation.x = t * 0.8 + i;
          child.rotation.z = t * 0.6 + i;
        }
      });
    }

    if (particles && sparkGeo && !reducedMotion) {
      const pos = sparkGeo.attributes.position.array;
      const vels = sparkGeo.userData.velocities;
      for (let i = 0; i < vels.length; i++) {
        pos[i * 3] += vels[i].x;
        pos[i * 3 + 1] += vels[i].y;
        pos[i * 3 + 2] += vels[i].z;
        vels[i].life += 0.012;
        if (vels[i].life > 1 || pos[i * 3 + 1] > 3) {
          pos[i * 3] = (Math.random() - 0.5) * 1.2;
          pos[i * 3 + 1] = -1.2;
          pos[i * 3 + 2] = (Math.random() - 0.5) * 1.2;
          vels[i].life = 0;
        }
      }
      sparkGeo.attributes.position.needsUpdate = true;
    }

    scene.rotation.y += (mouseX * 0.35 - scene.rotation.y) * 0.04;
    scene.rotation.x += (mouseY * 0.25 - scene.rotation.x) * 0.04;

    renderer.render(scene, camera);
  }

  function init(el) {
    if (!el || !window.THREE || renderer) return;

    reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    container = el;

    scene = new THREE.Scene();
    camera = new THREE.PerspectiveCamera(45, 1, 0.1, 100);
    camera.position.set(0, 0.2, 10);

    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0x000000, 0);
    el.appendChild(renderer.domElement);

    buildCore();
    buildOrbitNodes();
    buildSparks();

    scene.position.y = 0;
    scene.scale.setScalar(1);

    window.addEventListener("resize", onResize);
    window.addEventListener("mousemove", onMouseMove);
    onResize();

    if (!reducedMotion) animate();
    else renderer.render(scene, camera);
  }

  window.Forge3D = {
    init: init,
    show: function () {
      visible = true;
      if (container) container.classList.remove("hidden");
      if (!animationId && !reducedMotion) animate();
    },
    hide: function () {
      visible = false;
      if (container) container.classList.add("hidden");
    },
  };

  document.addEventListener("DOMContentLoaded", function () {
    init(document.getElementById("forge3d"));
  });
})();
