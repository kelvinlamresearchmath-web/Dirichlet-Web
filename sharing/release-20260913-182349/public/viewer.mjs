import * as pdfjs from './vendor/pdfjs/build/pdf.mjs';
pdfjs.GlobalWorkerOptions.workerSrc = './vendor/pdfjs/build/pdf.worker.mjs';
const $ = id => document.getElementById(id);
const book = window.BOOK;
const chapter = $('chapter');
let pdf, requestedPage = Math.min(book.pages, Math.max(1, Number(/^#page=(\d+)$/.exec(location.hash)?.[1]) || 13));
let rendering = false, pending = false;
chapter.options[0].value = '';
for (const [index, item] of book.chapters.entries()) {
  const option = document.createElement('option');
  option.value = String(index);
  option.textContent = `${item.depth ? '　' : ''}${item.title}`;
  chapter.appendChild(option);
}
async function renderPage() {
  if (!pdf) return;
  if (rendering) { pending = true; return; }
  rendering = true;
  $('status').textContent = '正在显示书页…';
  const number = requestedPage;
  try {
    const page = await pdf.getPage(number);
    const base = page.getViewport({ scale: 1 });
    const width = Math.max(240, Math.min(1100, $('reading-area').clientWidth - 40));
    const scale = $('zoom').value === 'fit' ? width / base.width : Number($('zoom').value);
    const viewport = page.getViewport({ scale });
    const ratio = Math.min(window.devicePixelRatio || 1, 2);
    const canvas = $('page-canvas');
    canvas.width = Math.ceil(viewport.width * ratio);
    canvas.height = Math.ceil(viewport.height * ratio);
    canvas.style.width = `${viewport.width}px`;
    canvas.style.height = `${viewport.height}px`;
    canvas.setAttribute('aria-label', `第 ${number} 页原版图像；文字版请使用打开原书链接`);
    await page.render({ canvasContext: canvas.getContext('2d'), viewport, transform: [ratio, 0, 0, ratio, 0, 0], background: '#ffffff' }).promise;
    $('page-number').value = String(number);
    $('prev').disabled = number === 1;
    $('next').disabled = number === book.pages;
    const index = book.chapters.findLastIndex(item => item.page <= number);
    chapter.value = index < 0 ? '' : String(index);
    history.replaceState(null, '', `#page=${number}`);
    $('status').textContent = '';
    $('reading-area').scrollTop = 0;
    page.cleanup();
  } catch (error) {
    $('status').textContent = '这一页未能显示，请切换页面重试，或使用下方链接打开原书。';
    console.error(error);
  } finally {
    rendering = false;
    if (pending) { pending = false; renderPage(); }
  }
}
function go(value) {
  requestedPage = Math.max(1, Math.min(book.pages, Math.trunc(Number(value) || 1)));
  renderPage();
}
chapter.addEventListener('change', () => { if (chapter.value !== '') go(book.chapters[Number(chapter.value)].page); });
$('cover').addEventListener('click', () => go(1));
$('prev').addEventListener('click', () => go(requestedPage - 1));
$('next').addEventListener('click', () => go(requestedPage + 1));
$('page-form').addEventListener('submit', event => { event.preventDefault(); go($('page-number').value); });
$('zoom').addEventListener('change', renderPage);
let resizeTimer;
window.addEventListener('resize', () => { clearTimeout(resizeTimer); resizeTimer = setTimeout(renderPage, 180); });
try {
  pdf = await pdfjs.getDocument({ url: book.file, cMapUrl: './vendor/pdfjs/cmaps/', cMapPacked: true, standardFontDataUrl: './vendor/pdfjs/standard_fonts/', wasmUrl: './vendor/pdfjs/wasm/', isEvalSupported: false, enableXfa: false }).promise;
  chapter.disabled = false;
  await renderPage();
} catch (error) {
  $('status').textContent = '书籍未能载入。请通过本地预览地址打开本页，或点击下方链接直接打开原书。';
  console.error(error);
}
