function registration() {
    const user = {
        username: document.getElementById('username').value.trim(),
        password: document.getElementById('password').value.trim(),
    };

    if (!user.username || !user.password) {
        alert("Пожалуйста, заполните все поля.");
        return;
    }

    const url = `/rest-api/users/registration`;
    const method = 'POST';

    fetch(url, {
        method: method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(user)
    })
    .then(function(resp) {
        if (resp.ok) {
            alert("Регистрация прошла успешно, можете войти в аккаунт");
            return resp.json();
        } else {
            return resp.json().then(err => {
                throw new Error(JSON.stringify(err));
            });
        }
    })
    .then(function(data) {
        console.log("Registration successful:", data);
    })
    .catch(function(error) {
        try {
            const errors = JSON.parse(error.message);
            if (errors.username)
                document.getElementById('username-error').innerText = errors.username;
            if (errors.password)
                document.getElementById('password-error').innerText = errors.password;
            if (errors.exception)
                document.getElementById('username-error').innerText = errors.exception;
        } catch (e) {
            document.getElementById('username-error').innerText = "Ошибка сервера: " + error.message;
        }
    });
}

function login() {
    const user = {
        username: document.getElementById('username').value,
        password: document.getElementById('password').value,
    };

    const url = `/rest-api/users/login`;
    const method = 'POST';

    fetch(url, {
        method: method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(user),
    })
    .then(function(resp) {
        if (resp.ok) {
            window.location.href = '/main'; 
        } else {
            return resp.json();
        }
    })
    .then(function(errors) {
        if (errors) {
            let errorMessage = '';
            if (errors.username) {
                errorMessage += errors.username + '\n';
            }
            if (errors.password) {
                errorMessage += errors.password + '\n';
            }
            if (errors.exception) {
                errorMessage += errors.exception + '\n';
            }

            alert('Ошибка входа:\n' + errorMessage);
        }
    })
    .catch(function(error) {
        console.error('Ошибка:', error);
        alert('Произошла ошибка при входе. Пожалуйста, попробуйте снова.');
    });
}

function openModal() {
    const modal = document.getElementById("profileModal");
    modal.style.display = "flex"; 
}

function closeModal() {
    const modal = document.getElementById("profileModal");
    modal.style.display = "none"; 
}

function submitProfile() {
    const formData = new FormData();
    formData.append("name", document.getElementById("name").value);
    formData.append("age", document.getElementById("age").value);
    formData.append("gender", document.getElementById("gender").value);
    formData.append("looking_for", document.getElementById("looking_for").value);
    formData.append("about", document.getElementById("about").value || "");

    fetch("/rest-api/profiles", {
        method: "POST",
        body: formData,
    })
    .then((response) => {
        if (response.ok) {
            alert("Анкета заполнена");
            const unavailableMessage = document.getElementById("unavailable-message");
            if (unavailableMessage) {
                unavailableMessage.style.display = "none"; 
            }
            closeModal(); 
            window.location.href = "/main"; 
        } else {
            return response.json();
        }
    })
    .then((errors) => {
        if (errors) {
            alert("Произошла ошибка: " + (errors.message || "Неизвестная ошибка"));
        }
    });
}

function openEditProfileModal() {
    const modal = document.getElementById("editProfileModal");
    modal.style.display = "flex"; 
}

function closeEditProfileModal() {
    const modal = document.getElementById("editProfileModal");
    modal.style.display = "none"; 
}

function submitEditProfile() {
    const formData = new FormData();
    formData.append("name", document.getElementById("edit-name").value);
    formData.append("age", document.getElementById("edit-age").value);
    formData.append("gender", document.getElementById("edit-gender").value);
    formData.append("looking_for", document.getElementById("edit-looking_for").value);
    formData.append("about", document.getElementById("edit-about").value || "");
    const isHidden = document.getElementById("edit-is_hidden").checked;
    formData.append("is_hidden", isHidden);

    fetch("/rest-api/profiles", {
        method: "PUT",
        body: formData,
    })
    .then((response) => {
        if (response.ok) {
            alert("Анкета обновлена");
            closeEditProfileModal(); 
            window.location.reload(); 
        } else {
            return response.json();
        }
    })
    .then((errors) => {
        if (errors) {
            alert("Произошла ошибка: " + (errors.message || "Неизвестная ошибка"));
        }
    });
}

function deleteAccount() {
    if (confirm('Вы уверены, что хотите удалить свой аккаунт? Вы не сможете восстановить его.')) {
        fetch('/rest-api/profiles/delete', {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({})
        })
        .then(response => {
            if (response.ok) {
                alert('Ваш аккаунт удален.');
                window.location.href = '/'; 
            } else {
                return response.json().then(data => { throw new Error(data.message); });
            }
        })
        .catch(error => {
            alert('Ваш аккаунт удален ');
        });
    }
}

function logout() {
    if (confirm('Вы уверены, что хотите выйти из аккаунта?')) {
        window.location.href = '/rest-api/logout';
    }
}

let offset = 0;  
const limit = 3; 

function translateGender(gender) {
    const genderMap = {
        "male": "мужской",
        "female": "женский"
    };
    return genderMap[gender] || gender; 
}

function searchProfiles(reset = true) {
    if (reset) offset = 0; 

    const name = document.getElementById('search-name').value.trim();
    const age = document.getElementById('search-age').value.trim();

    const params = new URLSearchParams();
    if (name) params.append('name', name);
    if (age) params.append('age', age);
    params.append('offset', offset);

    fetch(`/rest-api/search?${params.toString()}`)
        .then(response => response.json())
        .then(data => {
            if (reset) {
                document.getElementById('search-results').innerHTML = ''; 
            }

            if (data.length > 0) {
                data.forEach(profile => {
                    const gender = translateGender(profile.gender); 

                    document.getElementById('search-results').innerHTML += `
                        <div class="profile-card">
                            <p><b>Имя:</b> ${profile.name}</p>
                            <p><b>Возраст:</b> ${profile.age}</p>
                            <p><b>Пол:</b> ${gender}</p>
                            <p><b>О себе:</b> ${profile.about || 'Не указано'}</p>
                        </div>
                    `;
                });
                offset += limit;
                document.getElementById('load-more-btn').style.display = 'block'; 
            } else if (reset) {
                document.getElementById('search-results').innerHTML = '<p>Анкеты не найдены</p>';
                document.getElementById('load-more-btn').style.display = 'none';
            } else {
                alert('Больше анкет не найдено');
                document.getElementById('load-more-btn').style.display = 'none';
            }
        })
        .catch(error => console.error('Ошибка:', error));
}

function loadMoreProfiles() {
    searchProfiles(false);
}