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

function generateTodosForActivity(activity) {
    const title = activity.toLowerCase();
    let todos = [];

    Object.entries(todoRules).forEach(([category, rules]) => {
        if (rules.keywords.some(keyword => title.includes(keyword))) {
            todos = todos.concat(rules.todos);
        }
    });

    if (todos.length === 0) {
        todos = [
            'Research location details',
            'Save contact information',
            'Set calendar reminder'
        ];
    }

    return todos;
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
    const activityRows = document.querySelectorAll('.activity-row');
    
    activityRows.forEach(row => {
        const todoItems = row.querySelector('.todo-items');
        const title = row.querySelector('.activity-title').firstChild.textContent.trim();
        
        if (!todoItems.children.length) {
            const generatedTodos = generateTodosForActivity(title);
            generatedTodos.forEach(todoText => {
                const todoItem = createTodoItem(todoText, false);
                todoItems.appendChild(todoItem);
            });
        }
    });

    // Save checkbox states
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
});

function toggleTodos(button) {
    const activityRow = button.closest('.activity-row');
    const todosContainer = activityRow.querySelector('.todo-items');
    const isHidden = todosContainer.style.display === 'none';
    
    // Debug logs
    console.log('Toggling todos');
    console.log('Is hidden:', isHidden);
    console.log('Todos container:', todosContainer);
    console.log('Todo items:', todosContainer.children);
    
    todosContainer.style.display = isHidden ? 'block' : 'none';
    button.textContent = isHidden ? '▲' : '▼';
    button.classList.toggle('active', isHidden);
} 