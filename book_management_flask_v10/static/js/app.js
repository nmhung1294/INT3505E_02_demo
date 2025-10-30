// Main application logic

let currentPage = 1;
let currentTab = 'books';

// Initialize app
document.addEventListener('DOMContentLoaded', async () => {
    await checkAuth();
    
    const isAuth = await TokenManager.isAuthenticated();
    if (isAuth) {
        initApp();
    }
});

async function initApp() {
    await setupUserInfo();
    setupTabs();
    setupEventListeners();
    loadBookTitles();
}

async function setupUserInfo() {
    const user = await TokenManager.getUserFromToken();
    if (user) {
        document.getElementById('user-id').textContent = `User ID: ${user.id}`;
    }
    
    document.getElementById('logout-btn').addEventListener('click', logout);
}

function setupTabs() {
    const tabs = document.querySelectorAll('.tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const tabName = tab.dataset.tab;
            switchTab(tabName);
        });
    });
}

function switchTab(tabName) {
    currentTab = tabName;
    
    // Update tab buttons
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.tab === tabName);
    });
    
    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.toggle('active', content.id === `${tabName}-tab`);
    });
    
    // Load data for the tab
    currentPage = 1;
    switch (tabName) {
        case 'books':
            loadBookTitles();
            break;
        case 'copies':
            loadBookCopies();
            break;
        case 'borrowings':
            loadBorrowings();
            break;
    }
}

function setupEventListeners() {
    // Add book title
    document.getElementById('add-book-btn').addEventListener('click', () => {
        openModal('add-book-modal');
    });
    
    document.getElementById('book-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        await addBookTitle();
    });
    
    // Add book copy
    document.getElementById('add-copy-btn').addEventListener('click', () => {
        openModal('add-copy-modal');
        loadBookTitlesForSelect();
    });
    
    document.getElementById('copy-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        await addBookCopy();
    });
    
    // Borrow book
    document.getElementById('borrow-btn').addEventListener('click', () => {
        openModal('borrow-modal');
        loadAvailableCopiesForSelect();
    });
    
    document.getElementById('borrow-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        await borrowBook();
    });
    
    // Close modals
    document.querySelectorAll('.close-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            closeModal(btn.closest('.modal').id);
        });
    });
    
    // Close modal on background click
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeModal(modal.id);
            }
        });
    });
}

function openModal(modalId) {
    document.getElementById(modalId).classList.add('active');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
    // Reset form if exists
    const modal = document.getElementById(modalId);
    const form = modal.querySelector('form');
    if (form) form.reset();
}

// Book Titles
async function loadBookTitles(page = 1) {
    try {
        document.getElementById('books-list').innerHTML = '<div class="loading">Loading...</div>';
        
        const data = await api.get(`/book_titles?page=${page}&size=10`);
        
        if (data.items.length === 0) {
            document.getElementById('books-list').innerHTML = `
                <div class="empty-state">
                    <h3>No books found</h3>
                    <p>Start by adding your first book</p>
                </div>
            `;
            return;
        }
        
        const html = `
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Title</th>
                        <th>Author</th>
                        <th>Publisher</th>
                        <th>Year</th>
                        <th>Category</th>
                        <th>Copies</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.items.map(book => `
                        <tr>
                            <td>${book.id}</td>
                            <td>${book.title}</td>
                            <td>${book.author}</td>
                            <td>${book.publisher || '-'}</td>
                            <td>${book.year || '-'}</td>
                            <td>${book.category || '-'}</td>
                            <td>${book.copies_count}</td>
                            <td>
                                <div class="actions">
                                    <button class="btn btn-secondary" onclick="viewBookDetails(${book.id})">View</button>
                                    <button class="btn btn-danger" onclick="deleteBook(${book.id})">Delete</button>
                                </div>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
            <div class="pagination">
                <button class="btn btn-secondary" onclick="loadBookTitles(${page - 1})" ${page === 1 ? 'disabled' : ''}>Previous</button>
                <span>Page ${data.page.page} of ${data.page.total_pages}</span>
                <button class="btn btn-secondary" onclick="loadBookTitles(${page + 1})" ${page >= data.page.total_pages ? 'disabled' : ''}>Next</button>
            </div>
        `;
        
        document.getElementById('books-list').innerHTML = html;
    } catch (error) {
        document.getElementById('books-list').innerHTML = `<div class="alert alert-error">${error.message}</div>`;
    }
}

async function addBookTitle() {
    try {
        const title = document.getElementById('book-title').value;
        const author = document.getElementById('book-author').value;
        const publisher = document.getElementById('book-publisher').value;
        const year = document.getElementById('book-year').value;
        const category = document.getElementById('book-category').value;
        
        await api.post('/book_titles', {
            title,
            author,
            publisher: publisher || null,
            year: year ? parseInt(year) : null,
            category: category || null
        });
        
        closeModal('add-book-modal');
        showAlert('Book added successfully!', 'success');
        loadBookTitles();
    } catch (error) {
        showAlert(error.message, 'error');
    }
}

async function deleteBook(id) {
    if (!confirm('Are you sure you want to delete this book?')) return;
    
    try {
        await api.delete(`/book_titles/${id}`);
        showAlert('Book deleted successfully!', 'success');
        loadBookTitles();
    } catch (error) {
        showAlert(error.message, 'error');
    }
}

async function viewBookDetails(id) {
    try {
        const book = await api.get(`/book_titles/${id}`);
        
        const html = `
            <h3>${book.title}</h3>
            <p><strong>Author:</strong> ${book.author}</p>
            <p><strong>Publisher:</strong> ${book.publisher || '-'}</p>
            <p><strong>Year:</strong> ${book.year || '-'}</p>
            <p><strong>Category:</strong> ${book.category || '-'}</p>
            <h4>Copies (${book.copies.length}):</h4>
            ${book.copies.length > 0 ? `
                <table>
                    <thead>
                        <tr>
                            <th>Barcode</th>
                            <th>Status</th>
                            <th>Condition</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${book.copies.map(copy => `
                            <tr>
                                <td>${copy.barcode}</td>
                                <td><span class="badge badge-${copy.available ? 'success' : 'danger'}">${copy.available ? 'Available' : 'Borrowed'}</span></td>
                                <td>${copy.condition}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            ` : '<p>No copies available</p>'}
        `;
        
        document.getElementById('view-details-content').innerHTML = html;
        openModal('view-details-modal');
    } catch (error) {
        showAlert(error.message, 'error');
    }
}

// Book Copies
async function loadBookCopies(page = 1) {
    try {
        document.getElementById('copies-list').innerHTML = '<div class="loading">Loading...</div>';
        
        const data = await api.get(`/book_copies?page=${page}&size=10`);
        
        if (data.items.length === 0) {
            document.getElementById('copies-list').innerHTML = `
                <div class="empty-state">
                    <h3>No book copies found</h3>
                    <p>Start by adding copies</p>
                </div>
            `;
            return;
        }
        
        const html = `
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Barcode</th>
                        <th>Book Title ID</th>
                        <th>Status</th>
                        <th>Condition</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.items.map(copy => `
                        <tr>
                            <td>${copy.id}</td>
                            <td>${copy.barcode}</td>
                            <td>${copy.book_title_id}</td>
                            <td><span class="badge badge-${copy.available ? 'success' : 'danger'}">${copy.available ? 'Available' : 'Borrowed'}</span></td>
                            <td>${copy.condition}</td>
                            <td>
                                <button class="btn btn-danger" onclick="deleteCopy(${copy.id})">Delete</button>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
            <div class="pagination">
                <button class="btn btn-secondary" onclick="loadBookCopies(${page - 1})" ${page === 1 ? 'disabled' : ''}>Previous</button>
                <span>Page ${data.page.page} of ${data.page.total_pages}</span>
                <button class="btn btn-secondary" onclick="loadBookCopies(${page + 1})" ${page >= data.page.total_pages ? 'disabled' : ''}>Next</button>
            </div>
        `;
        
        document.getElementById('copies-list').innerHTML = html;
    } catch (error) {
        document.getElementById('copies-list').innerHTML = `<div class="alert alert-error">${error.message}</div>`;
    }
}

async function loadBookTitlesForSelect() {
    try {
        const data = await api.get('/book_titles?page=1&size=100');
        const select = document.getElementById('copy-book-title');
        select.innerHTML = '<option value="">Select a book</option>' + 
            data.items.map(book => `<option value="${book.id}">${book.title} by ${book.author}</option>`).join('');
    } catch (error) {
        showAlert(error.message, 'error');
    }
}

async function addBookCopy() {
    try {
        const book_title_id = document.getElementById('copy-book-title').value;
        const barcode = document.getElementById('copy-barcode').value;
        const condition = document.getElementById('copy-condition').value;
        
        await api.post('/book_copies', {
            book_title_id: parseInt(book_title_id),
            barcode,
            condition
        });
        
        closeModal('add-copy-modal');
        showAlert('Book copy added successfully!', 'success');
        loadBookCopies();
    } catch (error) {
        showAlert(error.message, 'error');
    }
}

async function deleteCopy(id) {
    if (!confirm('Are you sure you want to delete this copy?')) return;
    
    try {
        await api.delete(`/book_copies/${id}`);
        showAlert('Copy deleted successfully!', 'success');
        loadBookCopies();
    } catch (error) {
        showAlert(error.message, 'error');
    }
}

// Borrowings
async function loadBorrowings(page = 1) {
    try {
        document.getElementById('borrowings-list').innerHTML = '<div class="loading">Loading...</div>';
        
        const data = await api.get(`/borrowings?page=${page}&size=10`);
        
        if (data.items.length === 0) {
            document.getElementById('borrowings-list').innerHTML = `
                <div class="empty-state">
                    <h3>No borrowings found</h3>
                    <p>Start by borrowing a book</p>
                </div>
            `;
            return;
        }
        
        const html = `
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Copy ID</th>
                        <th>User ID</th>
                        <th>Borrow Date</th>
                        <th>Due Date</th>
                        <th>Return Date</th>
                        <th>Fine</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.items.map(borrowing => `
                        <tr>
                            <td>${borrowing.id}</td>
                            <td>${borrowing.book_copy_id}</td>
                            <td>${borrowing.user_id}</td>
                            <td>${new Date(borrowing.borrow_date).toLocaleDateString()}</td>
                            <td>${borrowing.due_date ? new Date(borrowing.due_date).toLocaleDateString() : '-'}</td>
                            <td>${borrowing.return_date ? new Date(borrowing.return_date).toLocaleDateString() : '-'}</td>
                            <td>${borrowing.fine || 0} VND</td>
                            <td>
                                ${borrowing.return_date ? 
                                    '<span class="badge badge-success">Returned</span>' : 
                                    borrowing.overdue ? 
                                        `<span class="badge badge-danger">Overdue (${borrowing.days_overdue} days)</span>` : 
                                        '<span class="badge badge-warning">Borrowed</span>'
                                }
                            </td>
                            <td>
                                ${!borrowing.return_date ? 
                                    `<button class="btn btn-success" onclick="returnBook(${borrowing.id})">Return</button>` : 
                                    '-'
                                }
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
            <div class="pagination">
                <button class="btn btn-secondary" onclick="loadBorrowings(${page - 1})" ${page === 1 ? 'disabled' : ''}>Previous</button>
                <span>Page ${data.page.page} of ${data.page.total_pages}</span>
                <button class="btn btn-secondary" onclick="loadBorrowings(${page + 1})" ${page >= data.page.total_pages ? 'disabled' : ''}>Next</button>
            </div>
        `;
        
        document.getElementById('borrowings-list').innerHTML = html;
    } catch (error) {
        document.getElementById('borrowings-list').innerHTML = `<div class="alert alert-error">${error.message}</div>`;
    }
}

async function loadAvailableCopiesForSelect() {
    try {
        const data = await api.get('/book_copies?page=1&size=100');
        const availableCopies = data.items.filter(copy => copy.available);
        
        const select = document.getElementById('borrow-copy');
        select.innerHTML = '<option value="">Select a book copy</option>' + 
            availableCopies.map(copy => `<option value="${copy.id}">Copy #${copy.id} - ${copy.barcode}</option>`).join('');
    } catch (error) {
        showAlert(error.message, 'error');
    }
}

async function borrowBook() {
    try {
        const book_copy_id = document.getElementById('borrow-copy').value;
        const due_date = document.getElementById('borrow-due-date').value;
        
        await api.post('/borrowings', {
            book_copy_id: parseInt(book_copy_id),
            due_date: due_date || null
        });
        
        closeModal('borrow-modal');
        showAlert('Book borrowed successfully!', 'success');
        loadBorrowings();
    } catch (error) {
        showAlert(error.message, 'error');
    }
}

async function returnBook(id) {
    if (!confirm('Mark this book as returned?')) return;
    
    try {
        const result = await api.post(`/borrowings/${id}/return`, {});
        
        let message = 'Book returned successfully!';
        if (result.fine > 0) {
            message += ` Fine: ${result.fine} VND`;
        }
        
        showAlert(message, 'success');
        loadBorrowings();
    } catch (error) {
        showAlert(error.message, 'error');
    }
}
