
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
        var search_metadata_id = $("div#search-metadata-id").text();
        location.href = "json/?rec_id="+search_metadata_id;
    });

    $("#results-xml").on("click", function(){
        var search_metadata_id = $("div#search-metadata-id").text();
        location.href = "xml/?rec_id="+search_metadata_id;
    });

    $("#results-link").on("click", function(){
        var search_metadata_id = $("div#search-metadata-id").text();
        location.href = "/?rec_id="+search_metadata_id;
    });

    $("#results-home").on("click", function(){
        location.href = "/";
    });
});