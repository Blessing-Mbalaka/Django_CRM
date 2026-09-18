/* Sample workspace. No persistence, integrations or network requests. */
window.Marketing = (() => {
  const key = value => {
    const d = new Date(value);
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
  };
  const today = key(new Date());
  const day = offset => { const d = new Date(`${today}T12:00:00`); d.setDate(d.getDate() + offset); return key(d); };
  const channels = ['WhatsApp', 'Email', 'Facebook', 'Instagram', 'TikTok', 'Website', 'Mobile App', 'Google/Search', 'SMS', 'Flyers/Posters', 'Radio', 'Print', 'Other'];
  const advertTypes = ['Website', 'Mobile App', 'Google/Search', 'Facebook', 'Instagram', 'TikTok', 'WhatsApp', 'Email', 'SMS', 'Local Business Directory', 'Newspaper/Magazine', 'Community Radio', 'Billboard', 'Flyer/Poster', 'Event/Sponsorship', 'Other'];
  const objectives = ['Increase Sales', 'Get More Customers', 'Promote Product', 'Promote Service', 'Promote Event', 'Build Awareness', 'Bring Back Customers'];
  const results = [
    ['WhatsApp', 500, 900, 60, 14, 4, 6400],
    ['Instagram', 900, 750, 55, 12, 3, 7200],
    ['Facebook', 1200, 900, 70, 16, 4, 8800],
    ['Google', 750, 650, 45, 10, 2, 4800],
    ['Website/App Adverts', 800, 600, 40, 8, 1, 4200],
    ['Referral', 0, 250, 30, 6, 1, 3100],
    ['Other', 700, 200, 20, 4, 1, 2000]
  ].map(([channel, spent, reach, enquiries, leads, customers, sales]) => ({ channel, spent, reach, enquiries, leads, customers, sales }));
  const campaigns = [
    ['spring', 'Spring Promotion', 'Increase Sales', ['WhatsApp', 'Instagram'], 1500, 'Active'],
    ['launch', 'New Product Launch', 'Promote Product', ['Website', 'Facebook'], 2000, 'Active'],
    ['heritage', 'Heritage Month Market', 'Promote Event', ['Flyers/Posters', 'Radio'], 1200, 'Active'],
    ['local', 'Meet Your Local Makers', 'Build Awareness', ['Google/Search', 'Instagram'], 1000, 'Active'],
    ['comeback', 'Customer Comeback', 'Bring Back Customers', ['Email'], 500, 'Completed']
  ].map(([id, name, objective, channels, budget, status], i) => ({ id, name, objective, channels, budget, status, product: 'Locally made homeware', audience: 'Local households and gift shoppers', location: 'Soweto, Johannesburg', start: day(-12 + i), end: day(i === 4 ? -1 : 10 + i * 3), description: 'Help neighbours discover quality products made by local businesses.', reach: [1542, 1286, 620, 482, 320][i] }));
  const ads = [
    ['ad1', 'Spring collection on Instagram', 'Instagram', 'Instagram', 'spring', 1500, 900, 750, 92, 55, 3, 7200, 'Live'],
    ['ad2', 'Local homeware on Facebook', 'Facebook', 'Facebook', 'launch', 1600, 1200, 900, 110, 70, 4, 8800, 'Live'],
    ['ad3', 'Community directory listing', 'Website', 'Neighbourhood Directory (sample)', 'local', 1000, 800, 600, 72, 40, 1, 4200, 'Live'],
    ['ad4', 'Weekend market flyer', 'Flyer/Poster', 'Market noticeboard (sample)', 'heritage', 800, 700, 200, 35, 20, 1, 2000, 'Ended']
  ].map(([id, name, type, publisher, campaign, budget, spent, reach, responses, enquiries, customers, sales, status]) => ({ id, name, type, publisher, campaign, budget, spent, reach, responses, enquiries, customers, sales, status, what: 'Product', audience: 'Local shoppers', location: 'Johannesburg', start: day(-8), end: day(status === 'Ended' ? -1 : 14), link: '' }));
  const brand = { name: 'Naledi Local Goods', slogan: 'Made local. Loved at home.', primary: '#175b46', secondary: '#d9ebd8', accent: '#ef8d55', font: 'Segoe UI', secondaryFont: 'Georgia', short: 'Thoughtful homeware, made by local hands.', long: 'We bring together practical, beautiful homeware from small South African makers. Visit our Soweto shop for gifts, everyday essentials and friendly advice.', phone: '011 555 0142', whatsapp: '072 555 0142', email: 'hello@example.com', website: 'https://example.com', location: 'Soweto, Johannesburg', facebook: '', instagram: '', tiktok: '', linkedin: '', logo: '' };
  const firstNames = ['Thandi', 'Sipho', 'Lerato', 'Nomsa', 'Amina', 'Kabelo', 'Zanele', 'Musa', 'Naledi', 'Bongani'];
  const surnames = ['Mokoena', 'Dlamini', 'Nkosi', 'Molefe', 'Naidoo', 'Khumalo', 'Botha'];
  const leads = Array.from({ length: 70 }, (_, i) => ({ id: `lead${i}`, name: `${firstNames[i % 10]} ${surnames[Math.floor(i / 10)]}`, contact: `customer${i + 1}@example.com`, campaign: campaigns[i % 5].id, source: results[i % 7].channel, date: day(-(i % 20)), status: i < 16 ? 'Converted' : i < 24 ? 'Contacted' : i < 32 ? 'Interested' : 'New', value: (i % 5 + 1) * 200 }));
  const emails = [
    { id: 'email1', name: 'Spring Sale Email', subject: 'A little something for your home', audience: 'All Customers', heading: 'Fresh finds for spring', message: 'Discover locally made homeware and enjoy our seasonal offers in store this week.', cta: 'Explore the collection', link: 'https://example.com', sendAt: day(1) + 'T09:00', status: 'Scheduled', sent: 0, delivered: 0, opened: 0, clicked: 0, enquiries: 0, customers: 0, image: '', template: 'Promotion' },
    { id: 'email2', name: 'Customer Comeback', subject: 'We would love to see you again', audience: 'Inactive Customers', heading: 'Your next local favourite awaits', message: 'Pop in to see what is new. Our team is ready to help you find something special.', cta: 'Visit us', link: 'https://example.com', sendAt: day(-4) + 'T10:00', status: 'Sent (sample)', sent: 320, delivered: 312, opened: 184, clicked: 42, enquiries: 7, customers: 3, image: '', template: 'Come Back Offer' }
  ];
  const content = [
    { id: 'content1', kind: 'poster', category: 'Posters', title: 'Spring, made local', message: 'Thoughtful pieces for a fresh start.', product: 'Homeware collection', price: 'From R150', promotion: '10% off selected items', start: today, end: day(14), template: '1', status: 'Draft', image: '' },
    { id: 'content2', kind: 'social', category: 'Social Posts', title: 'Meet the makers', caption: 'Good things are made close to home. Discover the people behind your favourites.', platform: 'Instagram Post', cta: 'Visit our shop', hashtags: '#ShopLocal #Soweto', status: 'Draft', image: '' },
    { id: 'content3', kind: 'poster', category: 'Promotions', title: 'Heritage market', message: 'A day for local food, craft and community.', product: 'Community market', price: 'Free entry', template: '3', status: 'Draft', start: day(7), end: day(7), image: '' },
    { id: 'content4', kind: 'poster', category: 'Images', title: 'Our local collection', message: 'Brand graphic for the spring collection.', product: 'Naledi Local Goods', template: '2', status: 'Draft', image: '' }
  ];
  const opportunities = [
    ['Websites', 'Community Business Directory', 'Johannesburg', 500, 8000, 'A monthly feature where neighbours find local shops and services.'],
    ['Mobile Apps', 'Neighbourhood Shopping App', 'Soweto', 650, 4200, 'Introduce your business to people shopping close to home.'],
    ['Social Media', 'Local Makers Community', 'Gauteng', 350, 3500, 'A sponsored community post for local products and services.'],
    ['Local Business Directories', 'Gauteng Service Finder', 'Gauteng', 450, 6000, 'A directory listing for trusted small-business services.'],
    ['Community Radio', 'Local Community Radio', 'Gauteng', 1200, 12000, 'A short spot reaching listeners on their morning commute.'],
    ['Newspapers', 'Neighbourhood Weekly', 'Johannesburg', 900, 7000, 'A quarter-page advert in a local weekly newspaper.'],
    ['Magazines', 'Local Living Magazine', 'Gauteng', 1100, 5000, 'A small advert alongside local lifestyle stories.'],
    ['Events', 'Weekend Makers Market', 'Soweto', 750, 1500, 'Introduce your products at a community market.'],
    ['Outdoor Advertising', 'Community Noticeboard', 'Johannesburg', 300, 2000, 'A poster placement near a busy local shopping area.']
  ].map(([type, publisher, location, price, reach, description], i) => ({ id: `op${i}`, type, publisher, location, price, reach, description, audience: 'Local consumers and households' }));
  const activities = [
    { id: 'event1', name: 'Heritage Month Promotion', type: 'Promotion', date: day(7), description: 'Prepare the in-store promotion and window poster.' },
    { id: 'event2', name: 'Meet the local makers', type: 'Event', date: day(9), description: 'Invite customers to meet our local suppliers.' },
    { id: 'event3', name: 'WhatsApp Customer Campaign', type: 'Campaign', date: day(10), description: 'Preview the customer offer with the team.' }
  ];
  const state = { page: 'dashboard', campaigns, ads, brand, leads, emails, content, opportunities, activities, results, period: '30 Days', month: new Date(new Date().getFullYear(), new Date().getMonth(), 1), filters: {} };
  const totals = () => results.reduce((sum, row) => { for (const name of ['spent', 'reach', 'enquiries', 'leads', 'customers', 'sales']) sum[name] += row[name]; return sum; }, { spent: 0, reach: 0, enquiries: 0, leads: 0, customers: 0, sales: 0 });
  return { state, today, day, key, channels, advertTypes, objectives, totals };
})();
