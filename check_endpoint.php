<?php
header('Access-Control-Allow-Origin: *');
header('Content-Type: application/json');

/* ---------- 1. 連線 ---------- */
$dsn  = 'mysql:host=sql212.infinityfree.com;dbname=if0_39336326_shopee_log;charset=utf8mb4';
$user = 'if0_39336326';
$pass = 'NeHmfdukdJyk7';
try {
    $pdo = new PDO($dsn, $user, $pass, [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION
    ]);
} catch (PDOException $e) {
    http_response_code(500);
    exit(json_encode(['error'=>'DB connect failed: '. $e->getMessage()]));
}

/* ---------- 2. 自動建表（若不存在） ---------- */
$pdo->exec("
    CREATE TABLE IF NOT EXISTS click_log (
        id        INT AUTO_INCREMENT PRIMARY KEY,
        real_url  VARCHAR(512) NOT NULL,
        status    ENUM('未知','有效','失效') DEFAULT '未知',
        added_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) DEFAULT CHARSET=utf8mb4
");

/* ---------- 3. 撈未知 ---------- */
if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    $limit = intval($_GET['limit'] ?? 10);
    $stmt  = $pdo->prepare("SELECT id, real_url FROM click_log WHERE status='未知' LIMIT :limit");
    $stmt->bindValue(':limit', $limit, PDO::PARAM_INT);
    $stmt->execute();
    echo json_encode($stmt->fetchAll(PDO::FETCH_ASSOC));
    exit;
}

/* ---------- 4. 回寫狀態 ---------- */
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $stmt = $pdo->prepare("UPDATE click_log SET status = :status WHERE id = :id");
    $stmt->execute([
        ':status' => $_POST['status'],
        ':id'     => $_POST['id']
    ]);
    echo json_encode(['result' => 'ok']);
}