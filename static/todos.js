// Todo generation rules
const todoRules = {
    transportation: {
        keywords: ['flight', 'plane', 'airport', 'train', 'bus', 'travel'],
        todos: [
            'Book transportation tickets',
            'Check visa requirements',
            'Save booking confirmation'
        ]
    },
    dining: {
        keywords: ['restaurant', 'dinner', 'lunch', 'dining', 'cafe', 'breakfast'],
        todos: [
            'Make restaurant reservation',
            'Check dress code',
            'Save restaurant contact info'
        ]
    },
    accommodation: {
        keywords: ['hotel', 'resort', 'airbnb', 'hostel', 'accommodation', 'check-in'],
        todos: [
            'Confirm reservation',
            'Save accommodation contact information',
            'Note check-in/out times'
        ]
    },
    attraction: {
        keywords: ['museum', 'gallery', 'park', 'tour', 'visit', 'attraction', 'show', 'concert'],
        todos: [
            'Book tickets in advance',
            'Check opening hours',
            'Save venue information'
        ]
    }
};

function generateTodosForActivity(title) {
    const titleLower = title.toLowerCase();
    let todos = [];

    Object.entries(todoRules).forEach(([category, rules]) => {
        if (rules.keywords.some(keyword => titleLower.includes(keyword))) {
            todos = todos.concat(rules.todos);
        }
    });

    return todos.length > 0 ? todos : [
        'Research location details',
        'Save contact information',
        'Set calendar reminder'
    ];
}

function createTodoItem(todo, completed = false) {
    const todoItem = document.createElement('div');
    todoItem.className = 'todo-item';
    todoItem.innerHTML = `
        <span class="todo-label">${todo}</span>
        <input type="checkbox" class="todo-checkbox" ${completed ? 'checked' : ''}>
    `;
    return todoItem;
}

// Initialize todos for each activity
document.addEventListener('DOMContentLoaded', function() {
    console.log('Setting up event handlers');
    
    document.querySelectorAll('.ai-help-btn').forEach(button => {
        button.addEventListener('click', function(e) {
            console.log('AI help button clicked');
            e.preventDefault();
            
            // Get the activity title from the data attribute
            const activityTitle = this.dataset.activityTitle;
            console.log('Activity title from data attribute:', activityTitle);
            
            if (activityTitle) {
                getAIHelp(activityTitle);
            } else {
                console.error('No activity title found');
            }
        });
    });

    // Initialize todos for each activity
    const activityRows = document.querySelectorAll('.activity-row');
    
    activityRows.forEach(row => {
        const todoItems = row.querySelector('.todo-items');
        const title = row.querySelector('.activity-title').textContent.trim();
        
        // Initialize todos if none exist
        if (!todoItems.children.length) {
            const generatedTodos = generateTodosForActivity(title);
            generatedTodos.forEach(todoText => {
                const todoItem = createTodoItem(todoText, false);
                todoItems.appendChild(todoItem);
            });
        }
    });

    // Handle checkbox changes
    document.addEventListener('change', async function(e) {
        if (e.target.matches('.todo-checkbox, .event-checkbox')) {
            const activityRow = e.target.closest('.activity-row');
            const todoItems = activityRow.querySelector('.todo-items');
            const activityId = todoItems.dataset.activityId;
            
            try {
                const response = await fetch('/api/trip/todos/save', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        activityId: activityId,
                        todos: Array.from(activityRow.querySelectorAll('.todo-item')).map(item => ({
                            text: item.querySelector('.todo-label').textContent,
                            completed: item.querySelector('.todo-checkbox').checked
                        })),
                        eventConfirmed: activityRow.querySelector('.event-checkbox').checked
                    })
                });

                if (!response.ok) {
                    throw new Error('Failed to save todo state');
                }
            } catch (error) {
                console.error('Error saving todo state:', error);
            }
        }
    });

    const callButton = document.querySelector('.call-button');
    if (callButton) {
        callButton.addEventListener('mouseover', function() {
            this.style.background = 'rgba(135, 150, 207, 0.5)';
            this.style.transform = 'translateY(-2px)';
        });
        callButton.addEventListener('mouseout', function() {
            this.style.background = 'rgba(135, 150, 207, 0.3)';
            this.style.transform = 'translateY(0)';
        });
    }
});

function toggleTodos(button) {
    const todoItems = button.nextElementSibling;
    button.classList.toggle('active');
    todoItems.classList.toggle('active');
    
    if (todoItems.classList.contains('active')) {
        todoItems.style.maxHeight = todoItems.scrollHeight + 'px';
        todoItems.style.opacity = '1';
    } else {
        todoItems.style.maxHeight = '0';
        todoItems.style.opacity = '0';
    }
}

// Add this helper function
function isDiningActivity(taskText) {
    const diningKeywords = [
        'restaurant', 
        'dinner', 
        'lunch', 
        'dining', 
        'cafe', 
        'breakfast', 
        'pizza',
        'grimaldi',
        'late lunch'
    ];
    
    const taskLower = taskText.toLowerCase();
    console.log('Checking dining keywords for:', taskLower);
    
    // Check each keyword individually and log the result
    diningKeywords.forEach(keyword => {
        if (taskLower.includes(keyword)) {
            console.log(`Match found: "${keyword}" in "${taskLower}"`);
        }
    });
    
    const result = diningKeywords.some(keyword => taskLower.includes(keyword));
    console.log('isDiningActivity final result:', result);
    return result;
}

// Add this function for the call feature
function callRestaurant(phoneNumber) {
    if (confirm('Would you like to call the restaurant now?')) {
        window.location.href = `tel:${phoneNumber}`;
    }
}

// Update the getAIHelp function
async function getAIHelp(taskText) {
    const outputDiv = document.getElementById('ai-output');
    const loadingDiv = document.getElementById('ai-loading');
    
    outputDiv.style.display = 'none';
    loadingDiv.style.display = 'block';
    
    try {
        const response = await fetch('/api/ai/todo-help', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ task: taskText })
        });
        
        const data = await response.json();
        loadingDiv.style.display = 'none';
        outputDiv.style.display = 'block';
        
        if (data.success) {
            outputDiv.innerHTML = `
                <h3 style="color: #8796cf; margin-bottom: 10px;">AI Assistance for:</h3>
                <p style="color: #8796cf; margin-bottom: 15px;">${taskText}</p>
                <div style="color: #6b7a9a; white-space: pre-line;">${data.response}</div>
            `;
        } else {
            outputDiv.innerHTML = `<p style="color: #ff6b6b;">Error: ${data.error}</p>`;
        }
    } catch (error) {
        loadingDiv.style.display = 'none';
        outputDiv.style.display = 'block';
        outputDiv.innerHTML = '<p style="color: #ff6b6b;">An error occurred while getting AI assistance</p>';
    }
} 