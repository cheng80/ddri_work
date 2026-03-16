const { chromium } = require('playwright');
const path = require('path');

async function main() {
  const root = '/Users/cheng80/Desktop/ddri_work';
  const htmlPath = path.resolve(root, 'works/04_presentation/02_ml_analysis_report/01_ddri_ml_analysis_report_a4_landscape.preview.html');
  const pdfPath = path.resolve(root, 'works/04_presentation/02_ml_analysis_report/01_ddri_ml_analysis_report_a4_landscape.pdf');

  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto(`file://${htmlPath}`, { waitUntil: 'networkidle' });
  await page.pdf({
    path: pdfPath,
    format: 'A4',
    landscape: true,
    printBackground: true,
    displayHeaderFooter: true,
    headerTemplate: '<div></div>',
    footerTemplate: `
      <div style="width:100%; font-size:10px; color:#475569; padding:0 12mm; box-sizing:border-box; text-align:center;">
        <span class="pageNumber"></span> / <span class="totalPages"></span>
      </div>
    `,
    margin: { top: '10mm', right: '12mm', bottom: '16mm', left: '12mm' }
  });
  await browser.close();
  console.log('pdf_written');
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
