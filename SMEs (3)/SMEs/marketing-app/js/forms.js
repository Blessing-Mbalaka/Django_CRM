/* Form schemas keep labels, options and fields easy to edit. */
(function (A) {
  const C = A.C, S = A.state;
  const campaignOptions = () => S.campaigns.map(c => [c.id, c.name]);
  const field = (name, label, type = 'text', choices = null, required = false) => ({ name, label, type, choices, required });
  const f = field;
  const schemas = {
    campaign: () => [f('name', 'Campaign Name', 'text', null, true), f('objective', 'Campaign Objective', 'select', A.objectives), f('product', 'Product / Service'), f('audience', 'Target Audience'), f('location', 'Location'), f('channels', 'Marketing Channels', 'checks', A.channels, true), f('start', 'Start Date', 'date', null, true), f('end', 'End Date', 'date', null, true), f('budget', 'Budget (R)', 'number', null, true), f('status', 'Status', 'select', ['Draft', 'Scheduled', 'Active', 'Completed', 'Paused']), f('description', 'Description', 'textarea')],
    advert: () => [f('name', 'Advert Name', 'text', null, true), f('what', 'What are you advertising?', 'select', ['Business', 'Product', 'Service', 'Promotion', 'Event']), f('type', 'Advertising Type', 'select', A.advertTypes), f('publisher', 'Platform / Publisher', 'text', null, true), f('audience', 'Target Audience'), f('location', 'Target Location'), f('start', 'Start Date', 'date', null, true), f('end', 'End Date', 'date', null, true), f('budget', 'Budget (R)', 'number', null, true), f('spent', 'Amount Spent (R)', 'number'), f('link', 'Advert Link', 'url'), f('campaign', 'Campaign', 'select', [['', 'No campaign'], ...campaignOptions()]), f('status', 'Status', 'select', ['Draft', 'Scheduled', 'Live', 'Paused', 'Ended'])],
    poster: () => [f('posterType', 'Poster Type', 'select', ['Promotion Poster', 'Product Advert', 'Service Advert', 'Event Poster', 'Business Announcement', 'Price List', 'Special Offer']), f('title', 'Title', 'text', null, true), f('message', 'Short Message', 'textarea'), f('product', 'Product / Service'), f('price', 'Price'), f('promotion', 'Promotion'), f('start', 'Start Date', 'date'), f('end', 'End Date', 'date'), f('phone', 'Contact Number', 'tel'), f('whatsapp', 'WhatsApp Number', 'tel'), f('website', 'Website', 'url'), f('image', 'Image Upload', 'file')],
    social: () => [f('title', 'Post Title', 'text', null, true), f('caption', 'Caption', 'textarea'), f('image', 'Image', 'file'), f('product', 'Product / Service'), f('cta', 'Call to Action'), f('hashtags', 'Hashtags'), f('platform', 'Platform', 'select', ['Instagram Post', 'Facebook Post', 'WhatsApp Status', 'TikTok Caption', 'Business Announcement']), f('schedule', 'Schedule Date / Time', 'datetime-local')],
    email: () => [f('name', 'Campaign Name', 'text', null, true), f('subject', 'Subject', 'text', null, true), f('audience', 'Audience', 'select', ['All Customers', 'New Customers', 'Repeat Customers', 'VIP Customers', 'Inactive Customers', 'Custom Group']), f('heading', 'Email Heading', 'text', null, true), f('message', 'Message', 'textarea'), f('cta', 'Call-to-Action Text'), f('link', 'Call-to-Action Link', 'url'), f('image', 'Image', 'file'), f('sendAt', 'Send Date / Time', 'datetime-local')],
    activity: () => [f('name', 'Activity Name', 'text', null, true), f('type', 'Activity Type', 'select', ['Campaign', 'Advert', 'Email', 'Social Post', 'Promotion', 'Event']), f('date', 'Date', 'date', null, true), f('description', 'Description', 'textarea')],
    brand: () => [f('logo', 'Business Logo', 'file'), f('name', 'Business Name', 'text', null, true), f('slogan', 'Slogan'), f('primary', 'Primary Colour', 'color'), f('secondary', 'Secondary Colour', 'color'), f('accent', 'Accent Colour', 'color'), f('font', 'Primary Font', 'select', C.fonts), f('secondaryFont', 'Secondary Font', 'select', C.fonts), f('short', 'Short Business Description', 'textarea'), f('long', 'Long Business Description', 'textarea'), f('phone', 'Phone', 'tel'), f('whatsapp', 'WhatsApp Number', 'tel'), f('email', 'Email', 'email'), f('website', 'Website', 'url'), f('location', 'Physical Location'), f('facebook', 'Facebook', 'url'), f('instagram', 'Instagram', 'url'), f('tiktok', 'TikTok', 'url'), f('linkedin', 'LinkedIn', 'url')]
  };
  const emailTemplates = ['Promotion', 'New Product', 'New Service', 'Customer Thank You', 'Come Back Offer', 'Business Announcement', 'Event Invitation', 'Monthly Update'];
  const templateText = {
    'Promotion': ['A special offer, just for you', 'Your next local favourite', 'Discover our latest offers and find something you will love.'],
    'New Product': ['Meet our newest arrival', 'Something new has arrived', 'We have a new addition to our locally made collection. Come and take a look.'],
    'New Service': ['A new way we can help', 'Made for your everyday needs', 'Discover our newest service, created with our community in mind.'],
    'Customer Thank You': ['Thank you for shopping local', 'You make a difference', 'Every purchase supports local makers. Thank you for being part of our story.'],
    'Come Back Offer': ['We would love to see you again', 'It has been a while', 'Visit us for a friendly welcome and a look at what is new.'],
    'Business Announcement': ['A little news from our team', 'Here is what is happening', 'We have an update to share with our customers and neighbours.'],
    'Event Invitation': ['You are invited', 'Let us get together', 'Join us for a day of local products, friendly faces and community.'],
    'Monthly Update': ['Your monthly local update', 'This month at our shop', 'Here is a look at our latest arrivals and upcoming events.']
  };
  function control(spec, value) {
    const { name, label, type, choices, required } = spec;
    const title = `${label}${required ? ' *' : ''}`;
    const extra = required ? 'required' : '';
    if (type === 'checks') return `<fieldset class="choice-group full"><legend>${title}</legend>${choices.map(choice => `<label><input type="checkbox" name="${name}" value="${C.esc(choice)}" ${(value || []).includes(choice) ? 'checked' : ''}> ${choice}</label>`).join('')}</fieldset>`;
    if (type === 'textarea') return `<label class="field full">${title}<textarea name="${name}" maxlength="4000">${C.esc(value || '')}</textarea></label>`;
    if (type === 'select') return `<label class="field">${title}<select name="${name}" ${extra}>${choices.map(option => { const [id, text] = Array.isArray(option) ? option : [option, option]; return `<option value="${C.esc(id)}" ${String(value) === id ? 'selected' : ''}>${C.esc(text)}</option>`; }).join('')}</select></label>`;
    if (type === 'file') return `<label class="field full">${title}<input name="${name}" type="file" accept="image/png,image/jpeg,image/webp,image/gif"><small>Local preview only. PNG, JPG, WebP or GIF, up to 5 MB.</small>${value ? C.image(value, 'Current image') : ''}</label>`;
    return `<label class="field">${title}<input name="${name}" type="${type}" value="${C.esc(value ?? (type === 'number' ? 0 : ''))}" ${extra} ${type === 'number' ? 'min="0" max="100000000" step="0.01"' : type === 'text' ? 'maxlength="250"' : ''}></label>`;
  }
  function render(kind, initial = {}) {
    const defaults = { start: A.today, end: A.day(14), date: A.today, name: '', channels: [], ...initial };
    if (kind === 'brand') Object.assign(defaults, S.brand);
    let templates = '';
    if (kind === 'poster') templates = `<fieldset class="template-picker"><legend>Choose a template</legend>${['1', '2', '3', '4'].map((id, i) => `<label><input type="radio" name="template" value="${id}" ${String(initial.template || '1') === id ? 'checked' : ''}><span class="template-thumb style-${id}"><b>${['Fresh finds', 'Made local', 'You’re invited', 'Special offer'][i]}</b><small>${['Classic', 'Bold', 'Framed', 'Minimal'][i]}</small></span></label>`).join('')}</fieldset>`;
    if (kind === 'email') templates = `<label class="field email-template">Email Template<select name="template" id="emailTemplate">${C.options(emailTemplates, initial.template || 'Promotion')}</select></label>`;
    const buttons = ['poster', 'social', 'email'].includes(kind)
      ? `<button class="btn secondary" type="submit" name="intent" value="preview">Preview</button><button class="btn secondary" type="submit" name="intent" value="draft">Save Draft</button>${kind === 'poster' ? '<button class="btn secondary" type="submit" name="intent" value="download">Download</button><button class="btn" type="submit" name="intent" value="share">Share</button>' : '<button class="btn" type="submit" name="intent" value="schedule">Schedule</button>'}${kind === 'email' ? '<button class="btn secondary" type="submit" name="intent" value="send">Send (demo)</button>' : ''}`
      : `<button class="btn" type="submit">${kind === 'brand' || initial.id ? 'Save Changes' : 'Create'}</button>`;
    return `<form data-form="${kind}" data-id="${initial.id || ''}"><div class="error" id="formError" role="alert"></div>${templates}<div class="form-grid">${schemas[kind]().map(spec => control(spec, defaults[spec.name])).join('')}</div><p class="small-copy muted">${['poster', 'social', 'email'].includes(kind) ? 'Your Brand Kit supplies the logo, business name, colours and contact details. Sending, sharing and downloads are demo actions.' : 'Changes are kept in this preview until the page is refreshed.'}</p><div class="form-actions">${C.btn('Cancel', 'close')}${buttons}</div><div id="formPreview" aria-live="polite"></div></form>`;
  }
  A.F = { render, schemas, templateText };
})(window.Marketing);
