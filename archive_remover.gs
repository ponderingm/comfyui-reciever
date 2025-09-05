/**
 * Google Apps Script: アーカイブフォルダ内の全ファイルを削除
 *
 * 使い方:
 * 1. Google DriveでアーカイブフォルダIDを取得
 * 2. archive_remover.gs をGASプロジェクトに貼り付け
 * 3. archiveFolderId を自分のIDに変更
 * 4. 手動またはトリガーで実行
 */

function removeAllFilesInArchiveFolder() {
  // アーカイブフォルダのIDを指定
  var archiveFolderId = 'YOUR_ARCHIVE_FOLDER_ID';
  var folder = DriveApp.getFolderById(archiveFolderId);
  var files = folder.getFiles();
  var count = 0;
  while (files.hasNext()) {
    var file = files.next();
    file.setTrashed(true); // ゴミ箱へ移動
    count++;
  }
  Logger.log('Deleted ' + count + ' files.');
}
