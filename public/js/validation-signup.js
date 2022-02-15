function validate_name(){
    let error_field = document.getElementById("error_name");
    let name = document.getElementsByTagName("form")[0]['name'].value;
    
    if (/[^a-zA-Z]/.test(name)){
        error_field.style.display = 'block';
        error_field.innerHTML="Name cannot contain special characters or digits";
    }

    else if(name.length <3){
        error_field.style.display = 'block';
        error_field.innerHTML="Name cannot be less than 3 characters.";
        return false;
    }

    else{
        error_field.style.display = 'none';
        error_field.innerHTML="";
        return true;
    }
}

function validate_age(){
    let error_field = document.getElementById("error_age");
    let age = Number(document.getElementsByTagName("form")[0]['age'].value);
    let error_string = "";

    if(age<3 || age>100){
        error_string = "Enter a valid age";
        error_field.style.display = 'block';
        error_field.innerHTML=error_string;
        return false;
    }
    else{
        error_field.style.display = 'none';
        error_field.innerHTML=error_string;
    }
}

function validate_password(){
    let error_field = document.getElementById("error_pass");
    let password = document.getElementsByTagName("form")[0]['password'].value;
    let error_string = "";

    if(password.length < 8){
        error_string = "Password needs to be atleast 8 characters.";
        error_field.style.display = 'block';
        error_field.innerHTML=error_string;
        return false;
    }   
    else{
        error_field.style.display = 'none';
        error_field.innerHTML=error_string;
        return true;
    }
}

