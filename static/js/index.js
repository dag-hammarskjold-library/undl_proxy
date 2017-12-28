
$(document).ready(function() {

    $("#checkAll").change(function () {
        $("input:checkbox").prop('checked', $(this).prop("checked"));
        
        if ($("input:checkbox").is(':checked')) {
            $('#check-label').text('Uncheck All');
        } else {
            $('#check-label').text('Check All');
    }
    });

    $("#results-json").on("click", function() {
        var json = $("div#context-result-json").text();
        document.getElementById("modal-document-data").innerHTML = json;
        $('#document_modal').modal("show");
    });

    $("#results-xml").on("click", function(){
        var xml = $("div#context-result-xml").text();
        document.getElementById("modal-document-data").innerHTML = xml;
        $('#document_modal').modal("show");

        // data = `<html><body><pre>` + xml + `</pre></body></html>`
        // myWindow = window.open("data:text/html," + encodeURIComponent(data),
        //                "_blank", "width=200,height=100");
        // myWindow.focus();
    });

    $("#results-home").on("click", function(){
        location.href = "/";
    });
});