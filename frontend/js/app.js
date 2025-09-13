// TBG-PIS Frontend Application
class TBGApp {
    constructor() {
        this.apiBase = 'http://localhost:5001/api';
        this.currentUser = null;
        this.currentTenant = 'default';
        this.currentLanguage = 'en';
        this.translations = {};
        this.accessToken = localStorage.getItem('accessToken');
        
        this.init();
    }
    
    async init() {
        await this.loadTranslations();
        this.setupEventListeners();
        
        if (this.accessToken) {
            this.showMainApp();
            await this.loadDashboard();
        } else {
            this.showLoginScreen();
        }
    }
    
    async loadTranslations() {
        try {
            const response = await fetch(`locales/${this.currentLanguage}.json`);
            this.translations = await response.json();
            this.updateUI();
        } catch (error) {
            console.error('Failed to load translations:', error);
        }
    }
    
    updateUI() {
        // Update all elements with data-i18n attribute
        document.querySelectorAll('[data-i18n]').forEach(element => {
            const key = element.getAttribute('data-i18n');
            if (this.translations[key]) {
                if (element.tagName === 'INPUT' && element.type !== 'submit') {
                    element.placeholder = this.translations[key];
                } else {
                    element.textContent = this.translations[key];
                }
            }
        });
        
        // Set RTL for Arabic
        if (this.currentLanguage === 'ar') {
            document.body.classList.add('rtl');
            document.documentElement.dir = 'rtl';
        } else {
            document.body.classList.remove('rtl');
            document.documentElement.dir = 'ltr';
        }
    }
    
    setupEventListeners() {
        // Login form
        const loginForm = document.getElementById('loginForm');
        if (loginForm) {
            loginForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.login();
            });
        }
        
        // Create project form
        const createProjectForm = document.getElementById('createProjectForm');
        if (createProjectForm) {
            createProjectForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.createProject();
            });
        }
    }
    
    async makeRequest(endpoint, options = {}) {
        const url = `${this.apiBase}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            'X-Tenant': this.currentTenant,
            ...options.headers
        };
        
        if (this.accessToken) {
            headers['Authorization'] = `Bearer ${this.accessToken}`;
        }
        
        try {
            const response = await fetch(url, {
                ...options,
                headers
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Request failed');
            }
            
            return data;
        } catch (error) {
            console.error('API Request failed:', error);
            throw error;
        }
    }
    
    async login() {
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        const tenant = document.getElementById('tenant').value;
        
        this.currentTenant = tenant;
        
        try {
            const response = await this.makeRequest('/auth/login', {
                method: 'POST',
                body: JSON.stringify({ username, password })
            });
            
            this.accessToken = response.access_token;
            this.currentUser = response.user;
            localStorage.setItem('accessToken', this.accessToken);
            localStorage.setItem('currentTenant', this.currentTenant);
            
            this.showMainApp();
            await this.loadDashboard();
            
        } catch (error) {
            this.showError('loginError', error.message);
        }
    }
    
    logout() {
        this.accessToken = null;
        this.currentUser = null;
        localStorage.removeItem('accessToken');
        localStorage.removeItem('currentTenant');
        this.showLoginScreen();
    }
    
    showLoginScreen() {
        document.getElementById('loginScreen').classList.remove('hidden');
        document.getElementById('mainApp').classList.add('hidden');
    }
    
    showMainApp() {
        document.getElementById('loginScreen').classList.add('hidden');
        document.getElementById('mainApp').classList.remove('hidden');
        
        if (this.currentUser) {
            document.getElementById('userInfo').textContent = 
                `${this.currentUser.full_name} (${this.currentUser.username})`;
        }
    }
    
    showSection(sectionName) {
        // Hide all sections
        document.querySelectorAll('.section').forEach(section => {
            section.classList.add('hidden');
        });
        
        // Remove active class from all nav links
        document.querySelectorAll('.sidebar-nav .nav-link').forEach(link => {
            link.classList.remove('active');
        });
        
        // Show selected section
        document.getElementById(sectionName + 'Section').classList.remove('hidden');
        
        // Add active class to corresponding nav link
        event.target.closest('.nav-link').classList.add('active');
        
        // Load section data
        this.loadSectionData(sectionName);
    }
    
    async loadSectionData(sectionName) {
        switch (sectionName) {
            case 'dashboard':
                await this.loadDashboard();
                break;
            case 'projects':
                await this.loadProjects();
                break;
            case 'tasks':
                await this.loadTasks();
                break;
            case 'fieldOps':
                await this.loadFieldOperations();
                break;
        }
    }
    
    async loadDashboard() {
        try {
            // Load dashboard stats
            const stats = await this.makeRequest('/dashboard/stats');
            
            document.getElementById('totalProjects').textContent = stats.projects.total;
            document.getElementById('totalTasks').textContent = stats.tasks.total;
            document.getElementById('activeWorkers').textContent = stats.field_operations.today;
            document.getElementById('todaysOps').textContent = stats.field_operations.today;
            
            // Load recent activity
            const activity = await this.makeRequest('/dashboard/recent-activity?limit=5');
            this.renderRecentActivity(activity);
            
            // Load my tasks
            const myTasks = await this.makeRequest('/dashboard/my-tasks?limit=5');
            this.renderMyTasks(myTasks);
            
        } catch (error) {
            console.error('Failed to load dashboard:', error);
        }
    }
    
    renderRecentActivity(activity) {
        const container = document.getElementById('recentActivity');
        
        if (activity.recent_projects.length === 0 && activity.recent_tasks.length === 0) {
            container.innerHTML = '<p class="text-muted">No recent activity</p>';
            return;
        }
        
        let html = '<div class="list-group list-group-flush">';
        
        // Recent projects
        activity.recent_projects.forEach(project => {
            html += `
                <div class="list-group-item">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <h6 class="mb-1">${project.name}</h6>
                            <p class="mb-1 text-muted">New project created</p>
                        </div>
                        <small>${new Date(project.created_at).toLocaleDateString()}</small>
                    </div>
                </div>
            `;
        });
        
        // Recent tasks
        activity.recent_tasks.forEach(task => {
            html += `
                <div class="list-group-item">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <h6 class="mb-1">${task.title}</h6>
                            <p class="mb-1 text-muted">New task created</p>
                        </div>
                        <small>${new Date(task.created_at).toLocaleDateString()}</small>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        container.innerHTML = html;
    }
    
    renderMyTasks(data) {
        const container = document.getElementById('myTasks');
        
        if (data.tasks.length === 0) {
            container.innerHTML = '<p class="text-muted">No tasks assigned</p>';
            return;
        }
        
        let html = '<div class="list-group list-group-flush">';
        
        data.tasks.forEach(task => {
            const statusColor = this.getStatusColor(task.status);
            const dueDate = task.due_date ? new Date(task.due_date).toLocaleDateString() : 'No due date';
            
            html += `
                <div class="list-group-item">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <h6 class="mb-1">${task.title}</h6>
                            <p class="mb-1 text-muted">${dueDate}</p>
                        </div>
                        <span class="badge bg-${statusColor}">${task.status}</span>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        container.innerHTML = html;
    }
    
    async loadProjects() {
        try {
            const response = await this.makeRequest('/projects/');
            this.renderProjects(response.projects);
        } catch (error) {
            console.error('Failed to load projects:', error);
            document.getElementById('projectsList').innerHTML = 
                '<div class="alert alert-danger">Failed to load projects</div>';
        }
    }
    
    renderProjects(projects) {
        const container = document.getElementById('projectsList');
        
        if (projects.length === 0) {
            container.innerHTML = '<p class="text-muted">No projects found</p>';
            return;
        }
        
        let html = '<div class="table-responsive"><table class="table table-striped">';
        html += `
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Code</th>
                    <th>Status</th>
                    <th>Progress</th>
                    <th>Manager</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
        `;
        
        projects.forEach(project => {
            const statusColor = this.getStatusColor(project.status);
            const progress = Math.round(project.progress_percentage);
            
            html += `
                <tr>
                    <td><strong>${project.name}</strong></td>
                    <td>${project.code || '-'}</td>
                    <td><span class="badge bg-${statusColor}">${project.status}</span></td>
                    <td>
                        <div class="progress" style="height: 20px;">
                            <div class="progress-bar" role="progressbar" 
                                 style="width: ${progress}%" 
                                 aria-valuenow="${progress}" aria-valuemin="0" aria-valuemax="100">
                                ${progress}%
                            </div>
                        </div>
                    </td>
                    <td>${project.manager_name || '-'}</td>
                    <td>
                        <button class="btn btn-sm btn-outline-primary" onclick="viewProject(${project.id})">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-secondary" onclick="editProject(${project.id})">
                            <i class="fas fa-edit"></i>
                        </button>
                    </td>
                </tr>
            `;
        });
        
        html += '</tbody></table></div>';
        container.innerHTML = html;
    }
    
    async loadTasks() {
        // This would load all tasks or user's tasks
        const container = document.getElementById('tasksList');
        container.innerHTML = '<p class="text-muted">Task management coming soon...</p>';
    }
    
    async loadFieldOperations() {
        try {
            const response = await this.makeRequest('/field-ops/operations?limit=20');
            this.renderFieldOperations(response.field_operations);
        } catch (error) {
            console.error('Failed to load field operations:', error);
            document.getElementById('fieldOpsList').innerHTML = 
                '<div class="alert alert-danger">Failed to load field operations</div>';
        }
    }
    
    renderFieldOperations(operations) {
        const container = document.getElementById('fieldOpsList');
        
        if (operations.length === 0) {
            container.innerHTML = '<p class="text-muted">No field operations found</p>';
            return;
        }
        
        let html = '<div class="table-responsive"><table class="table table-striped">';
        html += `
            <thead>
                <tr>
                    <th>Type</th>
                    <th>Title</th>
                    <th>Project</th>
                    <th>User</th>
                    <th>Date</th>
                    <th>Status</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
        `;
        
        operations.forEach(op => {
            const statusColor = this.getStatusColor(op.status);
            const date = new Date(op.operation_date).toLocaleDateString();
            
            html += `
                <tr>
                    <td><span class="badge bg-info">${op.operation_type}</span></td>
                    <td>${op.title}</td>
                    <td>${op.project_name || '-'}</td>
                    <td>${op.user_name}</td>
                    <td>${date}</td>
                    <td><span class="badge bg-${statusColor}">${op.status}</span></td>
                    <td>
                        <button class="btn btn-sm btn-outline-primary" onclick="viewFieldOp(${op.id})">
                            <i class="fas fa-eye"></i>
                        </button>
                    </td>
                </tr>
            `;
        });
        
        html += '</tbody></table></div>';
        container.innerHTML = html;
    }
    
    getStatusColor(status) {
        const colors = {
            'active': 'success',
            'completed': 'success',
            'in_progress': 'primary',
            'pending': 'warning',
            'approved': 'success',
            'rejected': 'danger',
            'planning': 'secondary',
            'paused': 'warning',
            'cancelled': 'danger',
            'not_started': 'secondary',
            'blocked': 'danger'
        };
        return colors[status] || 'secondary';
    }
    
    showCreateProject() {
        const modal = new bootstrap.Modal(document.getElementById('createProjectModal'));
        modal.show();
    }
    
    async createProject() {
        const formData = {
            name: document.getElementById('projectName').value,
            code: document.getElementById('projectCode').value,
            description: document.getElementById('projectDescription').value,
            start_date: document.getElementById('projectStartDate').value,
            end_date: document.getElementById('projectEndDate').value,
            budget: parseFloat(document.getElementById('projectBudget').value) || 0,
            location: document.getElementById('projectLocation').value
        };
        
        try {
            await this.makeRequest('/projects/', {
                method: 'POST',
                body: JSON.stringify(formData)
            });
            
            // Close modal and refresh projects
            const modal = bootstrap.Modal.getInstance(document.getElementById('createProjectModal'));
            modal.hide();
            
            // Clear form
            document.getElementById('createProjectForm').reset();
            
            // Refresh projects list
            await this.loadProjects();
            
            this.showAlert('Project created successfully!', 'success');
            
        } catch (error) {
            this.showAlert('Failed to create project: ' + error.message, 'danger');
        }
    }
    
    async checkIn() {
        // Simple check-in - would need project selection in real implementation
        try {
            await this.makeRequest('/field-ops/attendance', {
                method: 'POST',
                body: JSON.stringify({
                    project_id: 1, // Default project - should be selected by user
                    attendance_type: 'check_in',
                    location: 'Field Site',
                    notes: 'Checked in via mobile app'
                })
            });
            
            this.showAlert('Check-in recorded successfully!', 'success');
            await this.loadFieldOperations();
            
        } catch (error) {
            this.showAlert('Failed to record check-in: ' + error.message, 'danger');
        }
    }
    
    async checkOut() {
        try {
            await this.makeRequest('/field-ops/attendance', {
                method: 'POST',
                body: JSON.stringify({
                    project_id: 1, // Default project - should be selected by user
                    attendance_type: 'check_out',
                    location: 'Field Site',
                    notes: 'Checked out via mobile app'
                })
            });
            
            this.showAlert('Check-out recorded successfully!', 'success');
            await this.loadFieldOperations();
            
        } catch (error) {
            this.showAlert('Failed to record check-out: ' + error.message, 'danger');
        }
    }
    
    showError(elementId, message) {
        const element = document.getElementById(elementId);
        element.textContent = message;
        element.classList.remove('hidden');
        
        setTimeout(() => {
            element.classList.add('hidden');
        }, 5000);
    }
    
    showAlert(message, type = 'info') {
        // Create a temporary alert
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Add to main content
        const mainContent = document.querySelector('.main-content');
        mainContent.insertBefore(alertDiv, mainContent.firstChild);
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            alertDiv.remove();
        }, 5000);
    }
}

// Language switching
async function changeLanguage(lang) {
    app.currentLanguage = lang;
    await app.loadTranslations();
    localStorage.setItem('preferredLanguage', lang);
}

// Initialize app
let app;
document.addEventListener('DOMContentLoaded', () => {
    // Load saved language preference
    const savedLang = localStorage.getItem('preferredLanguage');
    if (savedLang) {
        app = new TBGApp();
        app.currentLanguage = savedLang;
    } else {
        app = new TBGApp();
    }
});

// Global functions for UI interactions
function showSection(sectionName) {
    app.showSection(sectionName);
}

function logout() {
    app.logout();
}

function showCreateProject() {
    app.showCreateProject();
}

function createProject() {
    app.createProject();
}

function checkIn() {
    app.checkIn();
}

function checkOut() {
    app.checkOut();
}

function viewProject(projectId) {
    // Placeholder for viewing project details
    app.showAlert('Project details view coming soon...', 'info');
}

function editProject(projectId) {
    // Placeholder for editing project
    app.showAlert('Project editing coming soon...', 'info');
}

function viewFieldOp(opId) {
    // Placeholder for viewing field operation details
    app.showAlert('Field operation details view coming soon...', 'info');
}