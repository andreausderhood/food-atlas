const {chromium}=require('playwright');
const path=require('path');
const fs=require('fs');
(async()=>{
const browser=await chromium.launch({headless:true});
const page=await browser.newPage({viewport:{width:1440,height:1000}});
const errors=[];page.on('pageerror',e=>errors.push(e.message));
const base='file://'+path.resolve('data/build/site')+'/';
await page.goto(base+'foods/apple.html');
await page.screenshot({path:'data/build/interview-apple.png',fullPage:true});
console.log('apple',await page.locator('h1').innerText(),'meters',await page.locator('[role=meter]:visible').count());
await page.locator('#science-mode').click();
if(await page.locator('details[data-science]:not([open])').count())throw Error('Science toggle failed');
await page.locator('#science-mode').click();
await page.goto(base+'index.html');
await page.locator('#q').fill('apple');
console.log('apple search',await page.locator('.card:visible').count());
await page.locator('#season-region').fill('CH');await page.locator('#season-region').dispatchEvent('change');
await page.locator('#season-mode').selectOption('fresh');
console.log('season',await page.locator('#season-context').innerText());
await page.locator('#season-mode').selectOption('');
await page.locator('#q').fill('');
await page.screenshot({path:'data/build/interview-index.png',fullPage:true});
await page.setViewportSize({width:390,height:844});
for(const name of ['index.html','foods/apple.html','foods/apple--honeycrisp.html','compare.html']){
 await page.goto(base+name);const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth);
 if(overflow)throw Error('Mobile overflow '+name);
 console.log('mobile',name,'no overflow');
}
await page.screenshot({path:'data/build/interview-mobile.png',fullPage:true});
await browser.close();
if(errors.length)throw Error(JSON.stringify(errors));console.log('Browser checks passed; no JS errors');
})().catch(e=>{console.error(e);process.exit(1)});
