
<map>
  <node ID="root" TEXT="算法测试系统">
    <node TEXT="ASR" ID="4a8d9cf286374a7240a59df6d16792ac" STYLE="bubble" POSITION="right">
      <node TEXT="模型管理" ID="7e3e9615a16523ba16a666a0a0557e47" STYLE="fork">
        <node TEXT="搜索" ID="5471e4fd77fb880dbaef366103d6c42b" STYLE="fork">
          <node TEXT="搜索模型名称，按照关键字模糊匹配即可" ID="b4bf7f0c1564acafa4f41350767cca86" STYLE="fork"/>
        </node>
        <node TEXT="模型列表" ID="e4959fb65b6b8372fcdcdf2e227942be" STYLE="fork">
          <node TEXT="显示字段：模型名称，语种，版本，尺寸，创建时间，操作：查看详情， 修改，删除" ID="bc1e9300a480db3779976e094afa3351" STYLE="fork"/>
          <node TEXT="操作说明：1.点击查看详情，2.点击修改，可进行修改操作；3.点击删除，可以进行删除操作" ID="de66ad4bd13aa39b23ac061b4db68d1a" STYLE="fork">
            <node TEXT="修改操作" ID="0c3b3bb42169b50c515304bd4970999f" STYLE="fork">
              <node TEXT="选择列表中的某项，可以进行修改，能修改的字段有：模型名称，模型版本，语种，尺寸。不可修改：模型文件。在修改弹窗也有“确认修改”和“取消”按钮，点击确认修改后，修改数据库中对应信息内容，内容当即生效且刷新列表；点击取消后，放弃修改，隐藏弹窗，不对该数据做任务操作，列表不要更新维持原样。" ID="d6dec7bf78f19968fcb726e156d47730" STYLE="fork"/>
            </node>
            <node TEXT="删除操作" ID="17b972bd67cc44e835f81a789cd0f34c" STYLE="fork">
              <node TEXT="选择列表中的某项，可以删除，点击删除，弹出二次确认框（是或否），点击是，做逻辑删除，更改数据库该列表的显示状态；" ID="a6c36d805a45a0fcb7152371f3520dae" STYLE="fork"/>
            </node>
            <node TEXT="查看详情" ID="fa3097e1c893c57a461532c1740cbefa" STYLE="fork">
              <node TEXT="弹出弹窗展示该模型详情，展示字段：模型名称，语种，版本，尺寸，创建时间，模型文件：列出上传文件夹中所有的文件名称以及文件大小；" ID="219c1b225719bdbf35efe7aaa85230cb" STYLE="fork"/>
            </node>
          </node>
          <node TEXT="按照创建时间倒序进行排查，意为最新的在最前面，每页最多显示15条数据，分页展示，应有上一页和下一页的标签；" ID="1106f52d946171a8667cc0a606b287a2" STYLE="fork"/>
        </node>
        <node TEXT="上传模型" ID="fdc94409046bacfcabd2b285cb165aa9" STYLE="fork">
          <node TEXT="点击上传按钮，弹出弹窗，弹窗中应有的字段：模型名称（必填项，需要进行必填校验，单行输入框-30个字以内），语种（单选，默认选择中文，选择项有：中、英、西、日、韩、俄、法、德、泰、意、阿），版本：（必填项，需要进行必填校验，单行输入框-30个字以内），尺寸（单选，默认选择base：base,small,large）,   模型文件（应该有上传按钮，点击上传后可以在本地选择文件夹进行上传，只能上传文件夹，选择后将文件夹的所有文件进行上传与展示）， 还应有提交上传与取消按钮。点击提交上传后，新建一条信息在数据库中，且展示在列表中，显示状态为1；点击取消则是放弃上传模型。" ID="8019630e6579d4b9babe41d19bee3054" STYLE="fork"/>
        </node>
      </node>
      <node TEXT="测试任务管理" ID="d70aed1d298264ecb43383d6b1567611" STYLE="fork">
        <node TEXT="任务列表" ID="aa1072390af6924d8c3a7482f20b86e0" STYLE="fork">
          <node TEXT="显示字段：任务名称、模型名字、数据集、创建时间、任务状态（进行中、运行完成）；操作按钮：运行结果（仅任务状态为【运行完成】才能有）" ID="71e383e8144c8757c0d09fa9ce460f56" STYLE="fork"/>
          <node TEXT="运行结果" ID="402b7dadd588bb5a1fcb5a7c3be3df86" STYLE="fork">
            <node TEXT="仅任务状态为【运行完成】才展示该按钮" ID="c64c57c6b446dc07a6f57ea312f51a8f" STYLE="fork"/>
            <node TEXT="点击运行结果，按照弹出新页面保留原页面的方式进入结果详情页" ID="9ae45b853bdb3fcef0417106253eb530" STYLE="fork">
              <node TEXT="结果详情页左侧：需要展示所有运行过该模型的数据集卡片列表，以及每个数据集的总音频数量，总时长，平均WER，RET，S替换错误的数量，I模型多误测的数量，D模型漏识别的数量，Hit命中数量；" ID="9d889711913712054ea21d7fce6adc8d" STYLE="fork"/>
              <node TEXT="结果详情页上方展示：任务名称、模型名字、创建时间、运行完成时间" ID="2a17cafa0d5bcbfc57e453814efff782" STYLE="fork"/>
              <node TEXT="结果详情页右侧：默认展示第一个数据集的信息。点击某个数据集卡片需要展示该数据集里面每个音频的运行结果信息，主要功能包含：音频名字，音频播放，Ref参考文本展示,模型预测文本展示，并且指出哪些字有问题，有问题的字需要用红色的进行标记；修改REF文本功能，修改成功后并且直接同步到数据池中。" ID="c94f836ee72eaf86317f233bd83350f3" STYLE="fork"/>
            </node>
          </node>
        </node>
        <node TEXT="创建任务" ID="54d756639476067820b848776c19de23" STYLE="fork">
          <node TEXT="点击【创建任务】按钮，弹出弹窗，弹窗中应有的字段：任务名称（必填项，需要进行必填校验，单行输入框-30个字以内）" ID="8e70ea40487708d82a2d6375ffb9201a" STYLE="fork"/>
        </node>
      </node>
      <node TEXT="数据集管理" ID="6be4c73df19aae0c39d62f9a5ab4f13f" STYLE="fork">
        <node TEXT="数据集列表" ID="c98d505a839182f95b3b7a609ce7b9bc" STYLE="fork">
          <node TEXT="新增" ID="268bc333fb17ec172e427f2557371d97" STYLE="fork">
            <node TEXT="弹窗新增的框，展示字段：数据集名称（必填项，需要进行必填校验，单行输入框-30个字以内）、语种（单选，默认选择中文，选择项有：中、英、西、日、韩、俄、法、德、泰、意、阿），还应有确认以及取消按钮，点击确认，新增成功" ID="65312b3504deb8b20376745379f7e604" STYLE="fork"/>
          </node>
          <node TEXT="修改" ID="78c5fdcca4d831cfb1ec594b5c6aee0a" STYLE="fork">
            <node TEXT="弹窗修改的框，可修改字段：数据集名称（读取之前的名字，必填项，需要进行必填校验，单行输入框-30个字以内）；确认以及取消按钮；点击确认，新增成功，点击取消，放弃修改" ID="19ec36256534c14960c025410fbe51d4" STYLE="fork"/>
          </node>
          <node TEXT="删除" ID="e8575b256f8071e346cc4edf5bf74096" STYLE="fork">
            <node TEXT="弹出删除，二次弹窗确认用户是否要删除（提示问题：当前删除操作会一并解除数据集中音频关系，确定删除吗？）；点击确认，删除成功，在数据库中的数据集与音频关联关系表，要删掉与该数据集这些关联关系的数据；点击取消，放弃删除" ID="997636e53420de2f3d86d24b646966a3" STYLE="fork"/>
          </node>
          <node TEXT="搜索" ID="d34a5cd546f72afaef0892c595064f8c" STYLE="fork">
            <node TEXT="支持按照名字查询，模糊匹配，按照时间倒序进行排列" ID="cb31d371148ded1e00222882ac13b1c3" STYLE="fork"/>
          </node>
          <node TEXT="列表展示" ID="21ff9228b2349e44b9c0c13b7e0805af" STYLE="fork">
            <node TEXT="默认展示10个数据集，按照时间倒序展示，展示字段：数据集名称，语种，创建时间，音频总数量，音频总时长" ID="5c841c10877b451850b7fa76eacb9b88" STYLE="fork"/>
            <node TEXT="分两栏展示，左侧展示数据集，右侧展示音频列表" ID="701ad02a76eb23eb89e69a7012c2a4df" STYLE="fork">
              <node TEXT="音频支持播放/暂停按钮、文本修改、全选/取消全选、移除、翻页功能" ID="5a39382dad776511dae0a31b6d645d1d" STYLE="fork">
                <node TEXT="支持播放/暂停操作，支持拖拽进度条按照进度条指定位置开始播的功能；播放和暂停用同一个按钮不同状态" ID="bf2a2e50cebcfd5f22324c65773c427c" STYLE="fork"/>
                <node TEXT="点击文本修改按钮，读出原来的文本展示在多行文本框中，并且可以进行文本修改编辑，点击OK按钮后是确认修改，鼠标移出多行文本框外视为放弃修改。该修改需要同步到数据池的数据中，也就是全部生效。" ID="1915b4ca109ef971724ac5b0c4721a7d" STYLE="fork"/>
                <node TEXT="全选可以批量移除该数据集，移除后在数据库表中删除关联关系数据" ID="b1f6f29eb9fc089e34479eeff9e96024" STYLE="fork"/>
                <node TEXT="有上一页，下一页功能，一页默认展示50条数据；" ID="fd75f8bccea05d5d11beb333a50e6cc1" STYLE="fork"/>
              </node>
            </node>
          </node>
        </node>
        <node TEXT="数据池" ID="9d40202dd65395d733f411bb0b946064" STYLE="fork">
          <node TEXT="数据池列表默认时间倒序排列，每页默认展示50条数据；需要展示的内容：音频名字、音频播放按钮、音频时长（默认单位是：秒），音频来源（单选：Sota1,Sota2,Sota3,gf,outside,cv15,30min）、文本修改按钮、文本（多行文本框，最多展示2行每行30字，点击后可以动态扩展查看全部文本内容），噪声（单选：安静、中低、中高、高噪），行业（单选：未知，经济，金融，医疗，旅游，美食，科技），关联数据集（需要展示该音频数据在哪些数据集中）" ID="f7b6b16802412a317f783fbe284217f7" STYLE="fork"/>
          <node TEXT="操作：音频播放按钮、文本修改、全选、删除、加入数据集、翻页功能" ID="a377849c775518a508a01488e7b948c7" STYLE="fork">
            <node TEXT="音频播放按钮" ID="05830517d42551b89a19bf6f7fc706ef" STYLE="fork">
              <node TEXT="支持播放/暂停操作，支持拖拽进度条按照进度条指定位置开始播的功能；播放和暂停用同一个按钮不同状态" ID="75fad3cdc2b6e7e91070869b7cb585cb" STYLE="fork"/>
            </node>
            <node TEXT="文本修改" ID="f6406c5cb7ffeb5db213681d75ff8c08" STYLE="fork">
              <node TEXT="点击文本修改按钮，读出原来的文本展示在多行文本框中，并且可以进行文本修改编辑，点击OK按钮后是确认修改，鼠标移出多行文本框外视为放弃修改" ID="3b8a92d5284e2c1989827598f0ce3142" STYLE="fork"/>
            </node>
            <node TEXT="全选" ID="b851615119aef24be489ae7d5787f52f" STYLE="fork">
              <node TEXT="点击全选，选中当前页所有内容；在已经被选中的状态下，再次点击全选则是取消全选；" ID="82e49e0720b1b17be6afb3df87464396" STYLE="fork"/>
            </node>
            <node TEXT="删除" ID="aee07ecac21be0581930a91a90c2c03b" STYLE="fork">
              <node TEXT="在单条下可以删除某条被选中的数据；在全选后点击删除，可以删除被选中的所有数据，删除需要弹窗后用户进行二次确认后再做操作，做逻辑删除，删除后音频有效状态改变，前端不再显示。" ID="6fab5761feb042f4a675201bf9374d71" STYLE="fork"/>
            </node>
            <node TEXT="加入数据集" ID="9b890ca8f1a7214fa9ff857357c1d726" STYLE="fork">
              <node TEXT="1.在单条下可以将某条被选中的数据音频加入到数据集中：点击按钮后，弹出数据集名称列表，按时间倒序进行排列；可以选择多个数据集，将该条音频加入到多个数据集中；" ID="87d015d1ee817cacb58f9f1b91f603ff" STYLE="fork"/>
              <node TEXT="2.在全选后点击加入数据集，弹出数据集名称列表，按时间倒序进行排列；可以选择多个数据集，将该条音频加入到多个数据集中；一个音频可以添加刀片多个数据集中；" ID="52dc99280b989f80d2e2d7a865991594" STYLE="fork"/>
            </node>
            <node TEXT="翻页功能" ID="abad7504ae6ad58d177bab9e3d8ba330" STYLE="fork">
              <node TEXT="有上一页，下一页功能，一页默认展示50条数据；" ID="1caf7ff136f2ee1bdb8cea9d9ab56880" STYLE="fork"/>
            </node>
          </node>
          <node TEXT="批量导入" ID="1ff6040eeac7e2786f2dab5ed730f74a" STYLE="fork">
            <node TEXT="支持下载导入模版" ID="bf3cdaea8792a1dff304d2c445a97a5c" STYLE="fork">
              <node TEXT="模版为excel文件，点击下载即可" ID="033c73f98d8d4d95f9910cd9f223272b" STYLE="fork"/>
            </node>
            <node TEXT="数据导入" ID="2691a5d3e7e6a195214f487d44090602" STYLE="fork">
              <node TEXT="支持按照表格文件进行数据导入，导入的字段有：音频名称，语种，音频路径，音频来源，噪声，行业，时长，文本" ID="4eda84ea28df3d6a29817bd101affbe2" STYLE="fork"/>
              <node TEXT="点击导入按钮，可选择本地.xlsx 文件进行上传，上传后需要有弹窗来读取excel的文件并且展示字段信息，确认导入的信息是否正确；点击“确认导入”，数据写入数据库中，点击取消，则放弃导入数据。" ID="dd2e086a1727f5fe2409808f63b90da3" STYLE="fork"/>
            </node>
          </node>
          <node TEXT="支持筛选功能" ID="78cb39f7c1ebd8396ce402ab8b41c59f" STYLE="fork">
            <node TEXT="按照语种筛选" ID="d24e7b067e5fb62a462d213ab34b4da4" STYLE="fork"/>
            <node TEXT="按照音频来源筛选" ID="836577da2ac4a000d1ecd531f65ab86e" STYLE="fork"/>
            <node TEXT="按照行业筛选" ID="07c8a67f1219eb1ce9ac00479bdc096e" STYLE="fork"/>
            <node TEXT="按照时长的范围筛选" ID="4f1678c4193553f93e067eff2776cefb" STYLE="fork"/>
            <node TEXT="按照噪声筛选" ID="36babf6aadea918ed18c8d8f53e513e5" STYLE="fork"/>
            <node TEXT="可以支持多条件筛选" ID="6009e7a723cd583393e1694b935f6c5f" STYLE="fork"/>
          </node>
        </node>
      </node>
      <node TEXT="数据库表设计" ID="12a709db11d33acab67f60abc223542c" STYLE="fork"/>
    </node>
    <node TEXT="MT" ID="c9f082170b75b7d8db63dc1691e32de6" STYLE="bubble" POSITION="right"/>
    <node TEXT="TTS" ID="09f81550046ba2e27b3b2a18d074d402" STYLE="bubble" POSITION="right"/>
  </node>
</map>