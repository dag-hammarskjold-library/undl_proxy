
$(document).ready(function() {

    $("#checkAll").change(function () {
        $("input:checkbox").prop('checked', $(this).prop("checked"));
    });

    $("#results-json").on("click", function() {
        console.log("Clicked");
        var json = $("div#context-result").text();
        document.getElementById("modal-document-data").innerHTML = json;
        $('#document_modal').modal("show");
    });
});