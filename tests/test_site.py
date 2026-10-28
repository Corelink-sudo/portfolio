"""Structural regression checks for the original single-file portfolio."""
from html.parser import HTMLParser
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
VOID_ELEMENTS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
}


class Document(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.elements = []
        self.stack = []
        self.errors = []
        self.doctype = None
        self.scripts = []
        self.inline_script = False
        self.feed(source)
        self.close()

    def handle_decl(self, declaration):
        self.doctype = declaration.lower()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.elements.append((tag, attrs))
        if tag == "script":
            self.inline_script = "src" not in attrs
        if tag not in VOID_ELEMENTS:
            self.stack.append(tag)

    def handle_data(self, data):
        if self.inline_script:
            self.scripts.append(data)

    def handle_endtag(self, tag):
        if tag == "script":
            self.inline_script = False
        if not self.stack or self.stack[-1] != tag:
            self.errors.append(f"Unexpected </{tag}> at line {self.getpos()[0]}")
        else:
            self.stack.pop()


class SiteTests(unittest.TestCase):
    def setUp(self):
        self.source = (ROOT / "index.html").read_text(encoding="utf-8")
        self.doc = Document(self.source)

    def test_document_structure(self):
        self.assertEqual(self.doc.doctype, "doctype html")
        self.assertEqual(self.doc.errors, [])
        self.assertEqual(self.doc.stack, [])
        tags = [tag for tag, _ in self.doc.elements]
        for tag in ("html", "head", "title", "body", "main", "h1"):
            self.assertEqual(tags.count(tag), 1, tag)
        self.assertIn(("html", {"lang": "en"}), self.doc.elements)
        self.assertTrue(any(tag == "meta" and attrs.get("name") == "viewport"
                            for tag, attrs in self.doc.elements))

    def test_navigation_and_original_design_hooks(self):
        ids = [attrs["id"] for _, attrs in self.doc.elements if "id" in attrs]
        self.assertEqual(len(ids), len(set(ids)), "Duplicate IDs")
        for _, attrs in self.doc.elements:
            href = attrs.get("href", "")
            if href.startswith("#"):
                self.assertIn(href[1:], ids)
        for target in ("hero", "work", "grade", "process", "proof", "pricing",
                       "contact", "fx", "player", "preloader"):
            self.assertIn(target, ids)
        for effect in (".grain", ".cursor-ring", "@keyframes gl1", ".mesh",
                       "initParticles", "Flip.from", "ScrollTrigger.create"):
            self.assertIn(effect, self.source)
        self.assertFalse((ROOT / "styles.css").exists())
        self.assertFalse((ROOT / "portfolio").exists())

    def test_hero_video_plays_once(self):
        videos = [attrs for tag, attrs in self.doc.elements
                  if tag == "video" and attrs.get("id") == "heroVideo"]
        self.assertEqual(len(videos), 1)
        self.assertNotIn("loop", videos[0])
        self.assertIn("muted", videos[0])
        self.assertIn("playsinline", videos[0])
        self.assertIn("heroVideo.src = CONFIG.heroVideo", self.source)
        self.assertIn("heroVideo.addEventListener('ended', () => { heroFinished = true; settleHero(); })", self.source)
        self.assertIn("!heroFinished && !heroVideo.ended", self.source)
        self.assertNotIn("heroVideo.currentTime =", self.source)
        self.assertIn('id="watchReel"', self.source)
        self.assertIn("openPlayer(CONFIG.reel", self.source)

    def test_hero_dissolves_before_finishing(self):
        self.assertIn("heroVideo.addEventListener('timeupdate'", self.source)
        self.assertIn("duration - heroVideo.currentTime <= Math.min(2, duration * .4)", self.source)
        self.assertIn("heroBackdrop.classList.add('is-settled')", self.source)
        self.assertIn(".hero-media.is-settled video{opacity:0}", self.source)
        self.assertIn("transition:opacity var(--hero-fade-duration,1.6s)", self.source)
        self.assertIn("if (!heroReady || !heroInView || document.hidden || reduce)", self.source)
        self.assertIn("heroReady = true;", self.source)
        video = next(attrs for tag, attrs in self.doc.elements
                     if tag == "video" and attrs.get("id") == "heroVideo")
        self.assertNotIn("autoplay", video)

    def test_hero_effects_are_decorative_and_motion_safe(self):
        layers = [attrs for _, attrs in self.doc.elements
                  if attrs.get("class") == "hero-atmosphere"]
        self.assertEqual(len(layers), 1)
        self.assertEqual(layers[0].get("aria-hidden"), "true")
        hexagons = [attrs for tag, attrs in self.doc.elements
                    if tag == "svg" and attrs.get("class", "").startswith("hero-hex ")]
        self.assertEqual(len(hexagons), 3)
        self.assertTrue(all(attrs.get("focusable") == "false" for attrs in hexagons))
        for feature in ("@keyframes hero-light-sweep", "@keyframes hero-hex-drift",
                        "if (fine && !reduce)", "--hero-light-x", "--hero-light-y",
                        "hero.effects-paused", "animation:none!important"):
            self.assertIn(feature, self.source)
        self.assertIn("hero.classList.toggle('effects-paused', !heroReady || !heroInView || document.hidden)", self.source)
        self.assertIn("cancelAnimationFrame(lightFrame)", self.source)

    def test_visible_ambient_effect_layers(self):
        for class_name, expected in (("hero-aurora", 1), ("hero-dust", 18), ("hero-trail", 3)):
            elements = [attrs for _, attrs in self.doc.elements
                        if attrs.get("class") == class_name]
            self.assertEqual(len(elements), expected, class_name)
        for keyframe in ("hero-aurora-flow", "hero-dust-float", "hero-trail-pass"):
            self.assertIn("@keyframes " + keyframe, self.source)
        self.assertIn(".hero.effects-paused .hero-aurora", self.source)
        self.assertIn(".hero-trail{display:none}", self.source)
        self.assertIn('src="assets/aurora.webp"', self.source)
        self.assertTrue((ROOT / 'assets' / 'aurora.webp').is_file())
        self.assertNotIn('feGaussianBlur', self.source)

    def test_hero_fade_releases_expensive_resources(self):
        self.assertIn("heroVideo.addEventListener('transitionend'", self.source)
        self.assertIn("heroVideo.removeAttribute('src')", self.source)
        self.assertIn("heroVideo.load()", self.source)
        self.assertIn("heroVideo.hidden = true", self.source)
        self.assertIn("setTimeout(completeHeroFade, seconds * 1000 + 150)", self.source)
        self.assertIn("if (!ambientSettled || particlesQueued", self.source)
        self.assertIn("requestIdleCallback(start", self.source)
        self.assertIn("const N = 350", self.source)
        self.assertIn("will-change:opacity", self.source)
        self.assertNotIn("feGaussianBlur", self.source)

    def test_controls_and_form_safety(self):
        for tag, attrs in self.doc.elements:
            if tag == "button":
                self.assertIn(attrs.get("type"), ("button", "submit"))
            if attrs.get("id") in ("menu", "player"):
                self.assertIn("inert", attrs)
        self.assertIn("Message not sent:", self.source)
        self.assertNotIn("// demo mode", self.source)
        self.assertIn('id="formStatus" role="status"', self.source)
        self.assertIn('role="group" aria-label="Filter projects"', self.source)

    def test_brand_assets_and_green_theme(self):
        marks = [attrs for tag, attrs in self.doc.elements
                 if tag == "img" and attrs.get("src") == "assets/jaguar-mark.png"]
        self.assertEqual(len(marks), 3, "Header, footer, and assistant should use the brand mark")
        for asset in ("jaguar-mark.png", "favicon.png"):
            self.assertTrue((ROOT / "assets" / asset).read_bytes().startswith(b"\x89PNG\r\n\x1a\n"))
        self.assertTrue((ROOT / "assets" / "jaguar.avif").is_file())
        self.assertIn('--c1:#3ba543; --c2:#8bbb33;', self.source)
        self.assertIn("getPropertyValue('--c1')", self.source)
        self.assertIn("getPropertyValue('--c2')", self.source)
        for previous_accent in ("#00e5ff", "#7b2fff", "#ff2d95", "0,229,255", "123,47,255", "255,45,149"):
            self.assertNotIn(previous_accent, self.source.lower())
        for tag, attrs in self.doc.elements:
            if tag == "img" and attrs.get("src", "").startswith("assets/"):
                self.assertTrue((ROOT / attrs["src"]).is_file())
        self.assertIn("name: 'JAGUAR'", self.source)

    def test_hexagon_cursor(self):
        self.assertIn('--cursor-shape:polygon(50% 0,93.3% 25%,93.3% 75%,50% 100%,6.7% 75%,6.7% 25%)', self.source)
        self.assertIn('clip-path:var(--cursor-shape)', self.source)
        outlines = [attrs for tag, attrs in self.doc.elements
                    if tag == "svg" and attrs.get("class") == "cursor-outline"]
        self.assertEqual(len(outlines), 1)
        self.assertEqual(outlines[0].get("aria-hidden"), "true")
        self.assertIn('vector-effect:non-scaling-stroke', self.source)
        self.assertIn('.cursor-ring.is-view{width:96px;height:96px;background:var(--grad)}', self.source)

    def test_assistant_interface(self):
        elements = {attrs["id"]: (tag, attrs) for tag, attrs in self.doc.elements if "id" in attrs}
        for target in ("assistantToggle", "assistantPanel", "assistantForm", "assistantInput", "assistantLog"):
            self.assertIn(target, elements)
        self.assertEqual(elements["assistantToggle"][1]["aria-controls"], "assistantPanel")
        self.assertIn("hidden", elements["assistantPanel"][1])
        self.assertIn("Portfolio guide", self.source)
        self.assertNotIn("Demo · No AI connected", self.source)
        self.assertIn("assistantEndpoint: ''", self.source)
        self.assertTrue((ROOT / "assistant.js").is_file())
        code = (ROOT / "assistant.js").read_text(encoding="utf-8")
        self.assertIn("endpoint.origin !== location.origin", code)
        self.assertIn("document.createTextNode(text)", code)
        self.assertNotIn("demo", code.lower())
        self.assertNotIn("scripted", code.lower())
        self.assertNotIn("innerHTML", code)
        self.assertNotIn("localStorage", code.replace("Nothing is saved to localStorage", ""))

    def test_assistant_typing_animation(self):
        code = (ROOT / "assistant.js").read_text(encoding="utf-8")
        self.assertIn("const REPLY_DELAY_MS = 5500", code)
        self.assertIn("const pending = typingIndicator()", code)
        self.assertIn("setTimeout(resolve, REPLY_DELAY_MS)", code)
        self.assertIn("Promise.allSettled", code)
        self.assertIn("@keyframes assistant-type", self.source)
        self.assertIn(".assistant-typing-dots span{animation:none!important", self.source)

    @unittest.skipUnless(shutil.which("node"), "Node.js needed for hero runtime checks")
    def test_hero_runtime(self):
        result = subprocess.run(
            ["node", "--test", str(ROOT / "tests" / "hero-runtime.cjs")],
            text=True, capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    @unittest.skipUnless(shutil.which("node"), "Node.js needed for JS syntax check")
    def test_inline_javascript_syntax(self):
        result = subprocess.run(
            ["node", "--check"], input="\n".join(self.doc.scripts),
            text=True, capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        assistant = subprocess.run(
            ["node", "--check", str(ROOT / "assistant.js")],
            text=True, capture_output=True, check=False,
        )
        self.assertEqual(assistant.returncode, 0, assistant.stderr)


if __name__ == "__main__":
    unittest.main()
