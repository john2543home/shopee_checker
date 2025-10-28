<?php
$dsn  = 'mysql:host=sql212.infinityfree.com;dbname=if0_39336326_shopee_log;charset=utf8mb4';
$user = 'if0_39336326';
$pass = 'NeHmfdukdJyk7';
try {
    $pdo = new PDO($dsn, $user, $pass, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
} catch (PDOException $e) {
    http_response_code(500);
    exit('DB: ' . $e->getMessage());
}