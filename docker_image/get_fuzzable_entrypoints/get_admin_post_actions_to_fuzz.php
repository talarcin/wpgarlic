<?php

include("/fuzzer/functions.php");
include('/var/www/html/wp-load.php');

foreach ($GLOBALS['wp_filter'] as $k => $v) {
        if (str_starts_with($k, "admin_post")) echo "ADMIN: " . $k . "\n";
}
