/* Mock records only. Replace this module with an API adapter in a later phase. */
window.Academy = (() => {
  const day = offset => { const d = new Date(); d.setDate(d.getDate() + offset); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`; };
  const paths = [
    ['foundations', 'Entrepreneurship Foundations', 'Foundations', ['Entrepreneurial Mindset', 'Identifying Business Opportunities', 'Idea Generation & Evaluation', 'Problem–Solution Fit', 'Lean Canvas for SMEs', 'Business Models', 'Starting & Formalising a Business in South Africa']],
    ['validation', 'Customer & Market Validation', 'Validate', ['Understanding Your Customer', 'Customer Personas', 'Customer Discovery & Interviews', 'Market Research for SMEs', 'Competitor Analysis', 'Testing Business Ideas', 'Product–Market Fit', 'Pricing Your Product or Service']],
    ['finance', 'Financial Management', 'Build', ['Financial Management for SMEs', 'Bookkeeping & Record Keeping', 'Cash-Flow Management', 'Budgeting & Forecasting', 'Costing & Pricing', 'Profit, Revenue & Break-Even', 'Separating Personal & Business Finances', 'Understanding Financial Statements']],
    ['marketing', 'Marketing & Sales', 'Grow', ['Building an SME Brand', 'Digital Marketing', 'Social Media Marketing', 'Creating Marketing Content', 'WhatsApp Business for SMEs', 'Customer Acquisition', 'Sales Fundamentals', 'E-commerce & Selling Online', 'Customer Retention']],
    ['operations', 'Business Operations & Digitalisation', 'Build', ['Running Efficient Business Operations', 'Inventory Management', 'Invoicing & Payments', 'Customer Relationship Management', 'Project & Task Management', 'Digital Tools for SMEs', 'Data for Business Decision-Making', 'AI for Small Businesses', 'Cybersecurity Basics']],
    ['compliance', 'South African Business & Compliance', 'Build', ['Registering & Formalising Your Business', 'SARS & Tax Basics', 'CIPC Basics', 'B-BBEE for SMEs', 'Employment & Labour Basics', 'POPIA & Customer Data', 'Contracts for Small Businesses', 'Intellectual Property', 'Tender & Procurement Readiness']],
    ['funding', 'Funding & Investment Readiness', 'Investment Ready', ['Understanding SME Funding in South Africa', 'Funding vs Loans vs Equity', 'Becoming Funding Ready', 'Preparing Financial Documents', 'Business Plans for Funding', 'Grant Applications', 'Pitch Deck Development', 'Pitching Your Business', 'Investor Readiness', 'Business Valuation Basics']],
    ['growth', 'Growth & Scale', 'Scale', ['Building a Growth Strategy', 'Scaling Operations', 'Building & Managing a Team', 'Founder Leadership', 'Governance for Growing Businesses', 'Strategic Partnerships', 'Enterprise Sales', 'Corporate Supplier Readiness', 'Export Readiness', 'Innovation & Technology for Growth']]
  ].map(([id, title, stage, titles]) => ({ id, title, stage, titles }));
  const outputs = {
    foundations: ['Complete a one-page Lean Canvas', 'Describe your customer, their problem, your offer, the costs and the next assumption to test.'],
    validation: ['Complete customer interviews', 'Write three open questions, speak to a potential customer and record what surprised you.'],
    finance: ['Build a cash-flow forecast', 'List opening cash, expected receipts and payments for the next four weeks. Use clearly labelled estimates.'],
    marketing: ['Create a marketing campaign', 'Choose one offer, one audience, one channel and a result you will measure.'],
    operations: ['Improve one business process', 'Map the steps, name the owner and choose a small change you can review next week.'],
    compliance: ['Prepare a compliance questions checklist', 'List the questions for your business and find the relevant official authority. This is not a compliance assessment.'],
    funding: ['Prepare a funding pack', 'Describe the funding need and list the documents and evidence you have available.'],
    growth: ['Create a practical growth plan', 'Choose a growth goal, identify a constraint and set a review date with your team.']
  };
  const modules = ['Getting Started', 'Understanding the Business Need', 'Practical Example', 'Guided Activity', 'Review Your Approach', 'Test Your Learning', 'Apply It to Your Business', 'Additional Resources', 'Reflect & Discuss'];
  const courses = paths.flatMap((path, p) => path.titles.map((title, i) => ({ id: `${path.id}-${i}`, title, path: path.id, category: path.title, stage: path.stage, level: p === 7 ? 'Intermediate' : 'Beginner', duration: 45 + i % 4 * 15, description: `Build practical skills in ${title.toLowerCase()} and leave with a next step for your business.`, output: [...outputs[path.id]], modules: [...modules], instructor: 'Academy facilitator · Sample instructor' })));
  courses.push({ id: 'idea', title: 'Idea Generation for South African SMEs', path: 'foundations', category: 'Entrepreneurship Foundations', stage: 'Foundations', level: 'Beginner', duration: 75, description: 'Explore useful business ideas and choose one customer problem to investigate.', output: ['Evaluate a business idea', 'List three ideas, describe the customer problem for each, and choose one assumption to test.'], modules: [...modules], instructor: 'Academy facilitator · Sample instructor' });
  const discovery = { ...courses.find(c => c.id === 'validation-2'), id: 'discovery', title: 'Customer Discovery & Market Validation' };
  discovery.modules = ['Getting Started', 'Understanding Your Customer', 'Customer Interviews', 'Guided Activity', 'Market Validation', 'Test Your Learning', 'Apply It to Your Business', 'Additional Resources', 'Reflect & Discuss'];
  courses.push(discovery);
  for (const course of courses.filter(c => /Pitch/.test(c.title))) course.output = ['Prepare your pitch deck', 'Create a short outline covering the customer problem, your offer, evidence, team and funding need. Select a sample file to represent your draft.'];
  const resources = [
    ['plan', 'One-page Business Plan', 'Business Plans', 'DOCX', ['Business overview', 'Customer need', 'Offer', 'Costs', 'Next steps']],
    ['canvas', 'Lean Canvas Worksheet', 'Lean Canvas', 'PDF', ['Problem', 'Customer', 'Value proposition', 'Channels', 'Revenue', 'Costs']],
    ['cash', 'Four-week Cash-Flow Forecast', 'Financial Templates', 'XLSX', ['Week', 'Opening cash', 'Receipts', 'Payments', 'Closing cash']],
    ['marketing', 'Simple Marketing Plan', 'Marketing Templates', 'DOCX', ['Offer', 'Audience', 'Channel', 'Budget', 'Measure']],
    ['pitch', 'Pitch Deck Outline', 'Pitch Deck Templates', 'PPTX', ['Problem', 'Solution', 'Customer evidence', 'Business model', 'Team', 'Ask']],
    ['hr', 'New Team Member Checklist', 'HR Templates', 'PDF', ['Role', 'Tools', 'Introduction', 'Training', 'Check-in']],
    ['compliance', 'Compliance Questions Checklist', 'Compliance Checklists', 'PDF', ['Topic', 'Authority', 'Question', 'Official source', 'Next step']],
    ['funding', 'Funding Pack Checklist', 'Funding Documents', 'PDF', ['Business plan', 'Records', 'Proof of sales', 'Funding need', 'Provider criteria']],
    ['research', 'Customer Interview Worksheet', 'Customer Research Templates', 'DOCX', ['Customer', 'Problem', 'Current approach', 'Interview notes', 'What to test']]
  ].map(([id, name, category, type, fields]) => ({ id, name, category, type, fields }));
  const mentors = [
    ['m1', 'Thandi Mokoena', 'Marketing & customer growth', 'Retail & services', 'Tuesday, 10:00'],
    ['m2', 'Sipho Dlamini', 'Finance & cash flow', 'Manufacturing & trade', 'Wednesday, 14:00'],
    ['m3', 'Amina Naidoo', 'Digital tools & operations', 'Technology & startups', 'Thursday, 11:00'],
    ['m4', 'Kabelo Molefe', 'Business planning & pitching', 'Agriculture & small business', 'Friday, 09:00']
  ].map(([id, name, expertise, industry, availability]) => ({ id, name, expertise, industry, availability }));
  const opportunities = ['Grants', 'Funding programmes', 'Competitions', 'Incubators', 'Accelerator programmes', 'Corporate supplier opportunities'].map((type, i) => ({ id: `op${i}`, title: ['Local Enterprise Starter Support', 'Small Business Equipment Programme', 'Neighbourhood Innovation Challenge', 'Business Foundations Incubator', 'Growth Builder Programme', 'Local Supplier Development'][i], provider: 'Sample enterprise support provider', type, deadline: day(14 + i * 3), eligibility: ['Early-stage South African businesses', 'Trading SMEs with organised records', 'Entrepreneurs testing a useful local idea', 'Founders developing a business model', 'SMEs ready to test a growth plan', 'Small businesses preparing to supply larger buyers'][i] }));
  const events = ['Webinar', 'Workshop', 'Masterclass', 'Networking', 'Pitching session'].map((type, i) => ({ id: `event${i}`, title: ['Your first customer interviews', 'Build a simple cash-flow forecast', 'Marketing that customers understand', 'Meet other local business owners', 'Practise your business pitch'][i], date: day(3 + i * 3), time: ['10:00', '14:00', '11:00', '16:00', '09:00'][i], mode: ['Online', 'In-person', 'Hybrid', 'In-person', 'Online'][i], type, location: i === 1 || i === 3 ? 'Johannesburg · Sample venue' : 'Sample event' }));
  const diagnostic = ['Business Model', 'Market', 'Customers', 'Product / Service', 'Finance', 'Operations', 'Technology', 'Marketing', 'Team', 'Intellectual Property', 'Funding Readiness', 'Growth', 'Scalability'];
  const posts = [
    { id: 'post1', title: 'How do you plan your week as a small team?', body: 'We have started a short Monday check-in. What helps your team stay focused?', author: 'Naledi M.', topic: 'Operations', kind: 'Question', replies: ['Sipho: We choose three priorities and give each one an owner.'] },
    { id: 'post2', title: 'Our first repeat customers', body: 'A simple follow-up routine helped us learn what customers wanted to buy again.', author: 'Kabelo M.', topic: 'Customer growth', kind: 'Success story', replies: [] },
    { id: 'post3', title: 'A useful way to prepare for supplier meetings', body: 'Write down your quantities, delivery needs and questions before you compare quotes.', author: 'Amina N.', topic: 'Business resources', kind: 'Resource', replies: [] }
  ];
  const completed = Object.fromEntries(courses.slice(0, 7).map(c => [c.id, [0, 1, 2, 3, 4, 5, 6, 7, 8]]));
  completed.idea = [0, 1, 2, 3, 4]; completed['finance-0'] = [0, 1, 2]; completed['marketing-1'] = [0, 1];
  const state = { page: 'dashboard', courseId: 'idea', module: 0, completed, outputs: {}, reflections: {}, quiz: {}, certificates: Object.fromEntries(courses.slice(0, 7).map(c => [c.id, day(-1)])), query: '', filters: { path: 'All', level: 'All', duration: 'All', stage: 'All', status: 'All' }, resourceCategory: 'All', profile: { name: 'Naledi', business: 'Naledi Local Goods', email: 'hello@example.com', location: 'Soweto, Johannesburg', industry: 'Retail', stage: 'Validate' }, diagnosticStep: 0, diagnosticAnswers: Array(13).fill(null), diagnosticFinished: false, sessions: [{ mentor: 'm1', date: day(4), time: '10:00', topic: 'Planning a local promotion' }], registrations: new Set(), posts, communityTopic: 'All', settings: { reminders: true, digest: false, compact: false }, activity: ['Completed: Starting & Formalising a Business in South Africa', 'Worked on: Idea Generation for South African SMEs'] };
  const progress = id => Math.round((state.completed[id]?.length || 0) / 9 * 100);
  const summary = () => ({ active: courses.filter(c => progress(c.id) > 0 && progress(c.id) < 100).length, completed: courses.filter(c => progress(c.id) === 100).length, hours: (courses.reduce((sum, c) => sum + c.duration * progress(c.id) / 100, 0) / 60).toFixed(1), certificates: Object.keys(state.certificates).length });
  return { state, paths, courses, resources, mentors, opportunities, events, diagnostic, day, progress, summary };
})();
