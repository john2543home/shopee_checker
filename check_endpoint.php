<?php
header('Access-Control-Allow-Origin: *');
header('Content-Type: application/json');

// ① 直接連資料庫（InfinityFree 值）
$dsn  = 'mysql:host=sql212.infinityfree.com;dbname=if0_39336326_shopee_log;charset=utf8mb4';
$user = 'if0_39336326';
$pass = 'NeHmfdukdJyk7';

try {
    $pdo = new PDO($dsn, $user, $pass, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
} catch (PDOException $e) {
    http_response_code(500);
    echo json_encode(['error' => 'DB connection failed']);
    exit;
}

// ② 撈「未知」連結
if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    $limit = intval($_GET['limit'] ?? 10);
    $sql   = "SELECT id, real_url FROM click_log WHERE status='未知' LIMIT :limit";
    $stmt  = $pdo->prepare($sql);
    $stmt->bindValue(':limit', $limit, PDO::PARAM_INT);
    $stmt->execute();
    echo json_encode($stmt->fetchAll(PDO::FETCH_ASSOC));
    exit;
}