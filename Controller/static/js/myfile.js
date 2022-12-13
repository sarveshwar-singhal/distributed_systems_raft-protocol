document.getElementById('showButton').onclick = function() 
{
    showMessage()
};

document.getElementById('saveButton').onclick = function()
{
    saveMessage()
};
/*
function showMessage(elem){
    document.getElementById('text_area').innerHTML = "This was created with Javascript";
}

function saveMessage(elem){
    // var msg = document.getElementById('temp').value;
    var msg = elem.value;
    console.log(msg);
}   */

function showMessage(){
    $.ajax({url: '/api/get_all_messages',
    type:"POST",
            success: function(result){
                console.log(result);
                document.getElementById('text_area').value = "";
                console.log(result.data);
                var value = result.data;
                var stringVal = "";
                document.getElementById('message_area').value = "";
                $.each(value,(element,v) => {
                    document.getElementById('message_area').value += element + ":\n";
                    var msgs = value[element]
                    msgs.forEach(msg => {
                        document.getElementById('message_area').value += msg + "\n";
                    });
                    document.getElementById('message_area').value += "\n ---------------------------------------\n";
                }); 
                // $("#text_area").text(stringVal)
               
            }});
  
}

function saveMessage(){
    var x = document.getElementById('text_area').value;
    // console.log(x);
    $.ajax({url: "/api/add_message",
            data:{'user_name':x},
            type:"POST",
            success: function(result){
                console.log(result);
                if(result['SUCCESS'] == true){
                    document.getElementById('text_area').value = "";
                    alert("Message inserted successfully");
                } else {
                    alert("Failure in Message insertion");
                }
                var res = ""
                for(var key in result['data']){
                    
                    res += "<p>"+key +" : "+ result['data'][key]+"</p>"
                }
                $("#last_request_status").html(res);
                showMessage();
            },
            error: function(errorMessage){
                console.log(errorMessage.responseText);
                alert("Error in API call");
            }
    });

    // $.ajax('/api/save',{
    //     type: 'POST',   //http method
    //     data: {myData: "this is my data"},
    //     success: function(result, status, xhr){
    //         console.log(result);
    //     },
    //     error: function(jgXhr, textStatus, errorMessage){
    //         console.log(errorMessage);
    //     }
    // });
}