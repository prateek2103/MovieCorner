function validate_username(){
    let error_field = document.getElementById("error_username");
    var reg = /^[A-Z0-9._%+-]+@([A-Z0-9-]+\.)+[A-Z]{2,4}$/i;
    let username = document.getElementsByTagName("form")[0]['username'].value;
    if(username.length==0){
        error_field.innerHTML="Username cannot be empty.";
        error_field.style.display="block";
    }

    else if(!reg.test(username)){
        error_field.innerHTML="Please enter a valid email id.";
        error_field.style.display="block"
    }
    else{
        error_field.innerHTML=""
        error_field.style.display="none";
    }
}

function validate_password(){
    let error_field = document.getElementById("error_pass");
    let pass = document.getElementsByTagName("form")[0]['password'].value;
    if(pass.length==0){
        error_field.innerHTML="Password cannot be empty.";
        error_field.style.display="block";
    }
    else{
        error_field.innerHTML=""
        error_field.style.display="none";
    }
}
