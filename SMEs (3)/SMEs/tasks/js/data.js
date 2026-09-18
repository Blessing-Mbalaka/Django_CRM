/* In-memory sample data. Reloading the page restores these examples. */
window.TaskApp = (() => {
  const dateKey = date => {
    const local = new Date(date);
    return `${local.getFullYear()}-${String(local.getMonth() + 1).padStart(2, '0')}-${String(local.getDate()).padStart(2, '0')}`;
  };
  const today = dateKey(new Date());
  const relativeDate = offset => {
    const date = new Date(`${today}T12:00:00`);
    date.setDate(date.getDate() + offset);
    return dateKey(date);
  };
  const team = [{
    id: 'thando',
    name: 'Thando M.',
    role: 'Operations lead',
    initials: 'TM'
  }, {
    id: 'naledi',
    name: 'Naledi K.',
    role: 'Marketing coordinator',
    initials: 'NK'
  }, {
    id: 'sipho',
    name: 'Sipho D.',
    role: 'Customer experience',
    initials: 'SD'
  }, {
    id: 'amina',
    name: 'Amina P.',
    role: 'Business administrator',
    initials: 'AP'
  }];
  const projects = [{
    id: 'website',
    name: 'Website Redesign',
    description: 'Improve our website and make it easier for customers to find what they need.',
    start: relativeDate(-20),
    due: relativeDate(20),
    owner: 'thando',
    members: ['thando', 'sipho'],
    status: 'Active'
  }, {
    id: 'marketing',
    name: `${new Date().toLocaleString('en-ZA', {month: 'long'})} Marketing Campaign`,
    description: 'Reach local customers with a focused email and social media campaign.',
    start: relativeDate(-10),
    due: relativeDate(14),
    owner: 'naledi',
    members: ['naledi', 'amina'],
    status: 'Active'
  }, {
    id: 'inventory',
    name: 'Stock Management Improvement',
    description: 'Organise the product catalogue and improve our stock receiving process.',
    start: relativeDate(-15),
    due: relativeDate(10),
    owner: 'thando',
    members: ['thando', 'amina'],
    status: 'Active'
  }, {
    id: 'customer',
    name: 'Customer Welcome Pack',
    description: 'Create a helpful welcome pack for every new customer.',
    start: relativeDate(-4),
    due: relativeDate(25),
    owner: 'sipho',
    members: ['sipho', 'naledi'],
    status: 'Active'
  }];
  const names = [
    ['Approve page layouts', 'Review website copy', 'Check mobile navigation', 'Prepare new product images', 'Update contact details', 'Test enquiry form', 'Review Customer Feedback', 'Publish the refreshed homepage'],
    ['Set campaign objectives', 'Confirm the audience', 'Draft the email', 'Choose campaign images', 'Prepare September Campaign', 'Schedule social posts', 'Review campaign budget', 'Approve launch checklist'],
    ['Count warehouse stock', 'Label storage shelves', 'Review supplier details', 'Check reorder levels', 'Archive old products', 'Document receiving process', 'Update Product Catalogue', 'Train the stock team'],
    ['Outline the welcome pack', 'Write the welcome message', 'Gather helpful resources', 'Review the first draft', 'Prepare the print layout', 'Share with the team']
  ];
  const completedCounts = [5, 3, 6, 4];
  let openIndex = 0;
  const tasks = projects.flatMap((project, group) => names[group].map((name, index) => {
    const completed = index < completedCounts[group];
    const position = completed ? -1 : openIndex++;
    const offset = completed ? -3 : position < 2 ? -2 : position < 8 ? 0 : position - 6;
    return {
      id: `task-${group}-${index}`,
      name,
      description: 'Work with the project team and review the result before completing this task.',
      project: project.id,
      assignee: team[(group + index) % team.length].id,
      due: relativeDate(offset),
      priority: ['Medium', 'High', 'Low'][index % 3],
      status: completed ? 'Completed' : index % 2 ? 'To Do' : 'In Progress',
      notes: '',
      attachment: ''
    };
  }));
  const state = {
    projects,
    tasks,
    team,
    currentUser: 'thando',
    page: 'dashboard',
    projectId: '',
    filter: 'All',
    search: '',
    view: 'list',
    personalTab: 'Today',
    month: new Date(new Date().getFullYear(), new Date().getMonth(), 1)
  };
  const overdue = task => task.status !== 'Completed' && task.due < today;
  const status = task => overdue(task) ? 'Overdue' : task.status;
  const projectTasks = id => state.tasks.filter(task => task.project === id);
  const progress = id => {
    const items = projectTasks(id);
    return items.length ? Math.round(items.filter(task => task.status === 'Completed').length / items.length * 100) : 0;
  };
  return {
    state,
    today,
    dateKey,
    relativeDate,
    overdue,
    status,
    projectTasks,
    progress
  };
})();
